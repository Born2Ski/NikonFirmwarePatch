/* HN31: which written frames have real previews, for Turbo RAW review with Auto N (HN30).
 *
 * The writer records every NEF it writes in C15/C20/C30/C60 (folder and file number from the NEF's DCF id, whether its
 * previews are real, the burst rate) in a RAM ring of RT_BITS frames. Runs of consecutive file numbers at one rate map
 * file numbers to ring positions (a burst's frames are consecutive file numbers of one folder). Turbo RAW review then
 * steps to the next frame with real previews at least 33 ms of capture time on, and shows each frame for the capture
 * time to the next one. RAM only: lost at power-off; frames not found here keep HN27's fixed-N stepping.
 * Pure code (no camera calls): also built on the host by the review table test. The includer defines u8/u16/u32.
 * noinline: one copy each (the pre-capture window has little room left). */
#define RT_RUNS 16u
#define RT_BITS 8192u                    /* frames remembered (a power of two) */
#define RT_MAGIC 0x31545652u             /* "RVT1" */
#define RT_NONE 0xffffffffu
typedef struct { u32 key, g; u16 count; u8 fps, spare; } rt_run;       /* key: folder << 14 | file number, first frame */
typedef struct {
    u32 magic, g, next, pend_key, pend_ms, spare[3];                   /* g: ring position of the next frame recorded */
    rt_run run[RT_RUNS];                                               /* next: the run slot used next (oldest) */
    u8 bits[RT_BITS/8u];                                               /* 1 = real previews */
} rt_t;
typedef char rt_size_check[sizeof(rt_t)==1248u?1:-1];

static u32 rt_key(u32 dcf) { return (dcf>>5)&0xffffffu; }             /* DCF id bits 5-18 file number, 19-28 folder */
static u32 rt_valid(const rt_t *t,u32 g) { return t->g-g-1u<RT_BITS; }  /* recorded and not yet overwritten */
static u32 rt_real(const rt_t *t,u32 g) { return (t->bits[(g/8u)%(RT_BITS/8u)]>>(g%8u))&1u; }

/* The writer, after a NEF is written: fps = the burst rate (0: not a C15/C20/C30/C60 frame), real = previews decoded. */
__attribute__((noinline)) static void rt_record(rt_t *t,u32 dcf,u32 fps,u32 real) {
    u32 key=rt_key(dcf),i,g; rt_run *r;
    if(!fps || fps>255u || !(key&0x3fffu)) return;
    if(t->magic!=RT_MAGIC) { for(i=0;i<sizeof(rt_t)/4u;i++) ((u32 *)t)[i]=0; t->magic=RT_MAGIC; }
    for(i=0;i<RT_RUNS;i++) {                       /* already recorded (the second card's copy): the same frame */
        r=&t->run[i];
        if(r->count && key-r->key<r->count && rt_valid(t,r->g+(key-r->key))) { g=r->g+(key-r->key); goto set; }
    }
    r=&t->run[(t->next+RT_RUNS-1u)%RT_RUNS];       /* the newest run, extended by the next file number */
    if(!(r->count && key==r->key+r->count && r->fps==fps && r->g+r->count==t->g && r->count<0xffffu)) {
        r=&t->run[t->next]; t->next=(t->next+1u)%RT_RUNS;
        r->key=key; r->g=t->g; r->count=0; r->fps=(u8)fps;
    }
    r->count++; g=t->g++;
set:
    if(real) t->bits[(g/8u)%(RT_BITS/8u)]|=(u8)(1u<<(g%8u));
    else t->bits[(g/8u)%(RT_BITS/8u)]&=(u8)~(1u<<(g%8u));
}

/* A recorded frame's ring position (newest run first), its burst rate and how many recorded frames follow it in its
 * run; RT_NONE if unknown. */
__attribute__((noinline)) static u32 rt_find(const rt_t *t,u32 dcf,u32 *fps,u32 *left) {
    u32 key=rt_key(dcf),i,g; const rt_run *r;
    if(t->magic!=RT_MAGIC) return RT_NONE;
    for(i=1;i<=RT_RUNS;i++) {
        r=&t->run[(t->next+RT_RUNS-i)%RT_RUNS];
        if(r->count && key-r->key<r->count) {
            g=r->g+(key-r->key);
            if(!rt_valid(t,g)) return RT_NONE;
            *fps=r->fps; *left=r->count-1u-(key-r->key);
            return g;
        }
    }
    return RT_NONE;
}

/* Frames from ring position g to the next real one at least 33 ms of capture time on, at most max (and within the
 * left recorded frames); 0 if there is none. */
__attribute__((noinline)) static u32 rt_step(const rt_t *t,u32 g,u32 left,u32 fps,u32 max) {
    u32 k=1u;
    while(1000u*k<33u*fps) k++;
    for(;k<=max && k<=left;k++) if(rt_valid(t,g+k) && rt_real(t,g+k)) return k;
    return 0;
}
static u32 rt_ms(u32 k,u32 fps) { u32 ms=(1000u*k+fps/2u)/fps; return ms<33u?33u:ms; }

/* Review step from file number f (ring position g, left recorded frames after it) inside a series that ends at file
 * number end (f < end): the target file number (the next real frame, else the series end) and how long to show it. */
__attribute__((noinline)) static u32 rt_plan(const rt_t *t,u32 f,u32 g,u32 left,u32 fps,u32 end,u32 *ms) {
    u32 k=rt_step(t,g,left,fps,end-f),at=k?f+k:end,k2;
    if(at>=end) { *ms=rt_ms(1u,fps); return end; }
    k2=at-f<=left?rt_step(t,g+(at-f),left-(at-f),fps,end-at):0u;
    *ms=rt_ms(k2?k2:end-at,fps);
    return at;
}
