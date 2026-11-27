/* z8nvme, HN29 "Fast card writes" (RAW extras row, own byte 0xA03D732A6): while the pre-capture writer writes a NEF (its markers 1 .. 6), the
 * CFexpress card is written faster, in three ways:
 *   - the slot's bus rate limiter is off (stock 0x110014 or 0x110020 at 0x1407B080/0x14083080 + slot * 0x10000; with it
 *     the card's DMA tops out at ~0.99 GB/s for limit 20);
 *   - root port and card use 512-byte packets (the largest both support; stock 128, ~1.6 GB/s on Gen3 x2 -> ~1.82);
 *   - the NVMe Flush the file system sends after each file is not sent while more frames of the burst are still waiting
 *     (writer marker 7); the burst's last NEF, written with nothing waiting, flushes as usual and covers everything.
 * Between NEFs and for everything else (other shooting, playback, video) the limiter and the packet size are stock again.
 * Measured on a ProGrade 512 GB (test firmwares n6/n7): RAW data 0.99 -> 1.82 GB/s, a NEF's write 42 -> ~21 ms, FX HE*
 * C30 bursts 106 -> 234 frames. Guard: a write that fails or takes over 0.4 s with these settings turns the limiter and
 * packet changes off until the camera restarts.
 *
 * Photo/RAW selections only: the unit lies at 0x40A12000 in the video groups' area. Its state is kept in the writable RAM
 * alias of that area (VA + 0x9CF600000): the loader maps the code window 0x40200000..0x40C00000 read-only.
 * Hook (z8nvme/patcher.py): the NVMe pass-through pointer (Private+0x58, set at 0x40271f48/0x40271f70; stock 0x402778b0).
 * The pre-capture writer calls +0x10 (markers) when the table's magic 'NVMD' at +0x14 is present. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long u64;

#define R8(a) (*(volatile const u8 *)(u64)(a))
#define R32(a) (*(volatile const u32 *)(u64)(a))
#define R64(a) (*(volatile const u64 *)(u64)(a))
#define W32(a,v) (*(volatile u32 *)(u64)(a)=(u32)(v))

#define PASSTHRU ((u32 (*)(u64,u32,u8 *,u64))0x402778b0ul)
#define SLOT0 0xa0280dd98ul        /* CFexpress slot records, 0x4b8 each */
#define SLOT_SIZE 0x4b8ul
#define RL_A 0x1407B080ul          /* bus rate limiter pair of slot 0; slot 1 at +0x10000 */
#define RL_B 0x14083080ul
#define DBI0 0x1A000000ul          /* DesignWare register base of controller i: DBI0 + i*0x400000 */
#define X_BYTE 0xa03d732a6ul       /* HN29 Fast card writes: 0 never set (On), else 0x80 | on (RAW extras row) */
#define ALIAS(va) ((va) - 0x40200000ul + 0xA0F800000ul)
#define S ((st_t *)ALIAS(0x40A1A000ul))

#define M_RL 1u
#define M_MPS 4u
#define M_FD 16u

typedef struct {
    u32 inited, want, applied, phase, more, bad;
    u64 freq;
    u32 rl_stock, rl_state;
    u64 dbi;
    u32 ep_cap, ep_mpss, rc_mpss, ep_devctl0, rc_devctl0, mps_on, mps_probed, fd_skipped;
} st_t;

static inline u64 cnt(void) { u64 v; __asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(v) :: "memory"); return v; }
static inline u64 cntfrq(void) { u64 v; __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(v)); return v; }
static void init(void) {
    if (S->inited == 0x4e565331u) return;
    for (u32 i = 0; i < sizeof(st_t) / 4; i++) ((volatile u32 *)S)[i] = 0;
    S->freq = cntfrq(); S->inited = 0x4e565331u;
}
static u32 fast_on(void) { u32 b = R8(X_BYTE); return (b & 0x80u) ? b & 1u : 1u; }          /* default On */

static u64 slot_rec(u32 *idx) {
    for (u32 s = 0; s < 2; s++) {
        u64 r = SLOT0 + s * SLOT_SIZE, proto = R64(r + 0xa0);
        if (proto && R32(proto - 0x48) == 0x454d564eu) { if (idx) *idx = s; return r; }
    }
    return 0;
}
typedef u32 (*cfgrw_t)(u64, u32, u32, u64, void *);
static u32 cfg_rd(u64 r, u32 off) { u32 v = 0xffffffffu; ((cfgrw_t)R64(r + 0x28 + 0x20))(r + 0x28, 2, off, 1, &v); return v; }
static void cfg_wr(u64 r, u32 off, u32 v) { ((cfgrw_t)R64(r + 0x28 + 0x28))(r + 0x28, 2, off, 1, &v); }
static u64 dbi_of(u64 r) { u64 h = R64(r + 0x88); u32 i = h ? R8(h + 0x27) : 9u; return i < 4 ? DBI0 + 0x400000ul * i : 0; }

static void mps_probe(u64 r) {
    if (S->mps_probed) return;
    S->mps_probed = 1;
    S->dbi = dbi_of(r);
    u32 p = cfg_rd(r, 0x34) & 0xfcu;
    for (u32 k = 0; k < 16 && p >= 0x40; k++) {
        u32 v = cfg_rd(r, p);
        if ((v & 0xffu) == 0x10u) { S->ep_cap = p; break; }
        p = (v >> 8) & 0xfcu;
    }
    if (S->ep_cap) { S->ep_mpss = cfg_rd(r, S->ep_cap + 4) & 7u; S->ep_devctl0 = cfg_rd(r, S->ep_cap + 8) & 0xffffu; }
    if (S->dbi) { S->rc_mpss = R32(S->dbi + 0x74) & 7u; S->rc_devctl0 = R32(S->dbi + 0x78) & 0xffffu; }
}
static void mps_set(u64 r, u32 on) {
    mps_probe(r);
    if (!S->ep_cap || !S->dbi) return;
    if (on) {
        u32 m = S->ep_mpss < S->rc_mpss ? S->ep_mpss : S->rc_mpss;           /* the largest both support, at most 512 B */
        if (m > 2) m = 2;
        if (m < 1) return;
        cfg_wr(r, S->ep_cap + 8, (S->ep_devctl0 & ~0xe0u) | m << 5);          /* the receiver first */
        W32(S->dbi + 0x78, (S->rc_devctl0 & ~0xe0u) | m << 5);
        S->mps_on = 1;
    } else if (S->mps_on) {
        W32(S->dbi + 0x78, S->rc_devctl0);                                    /* the transmitter back first */
        cfg_wr(r, S->ep_cap + 8, S->ep_devctl0);
        S->mps_on = 0;
    }
}
static void rl_set(u64 r, u32 s, u32 off) {
    if (!S->rl_stock) {                       /* as the slot set it: 0x110014 if Identify byte 0xC0D >= 4, else 0x110020 */
        u64 p = R64(r + 0xa0) - 0x48, cd = R64(p + 0x88);
        S->rl_stock = (cd && R8(cd + 0xc0d) >= 4) ? 0x110014u : 0x110020u;
    }
    u32 v = off ? 1u : S->rl_stock;
    W32(RL_A + 0x10000ul * s, v); W32(RL_B + 0x10000ul * s, v);
    S->rl_state = off;
}
/* Between commands only: the pass-through is serialised by the driver. */
static void apply(void) {
    if (S->applied == S->want) return;
    u32 s = 0; u64 r = slot_rec(&s), d = S->applied ^ S->want;
    if (!r) return;
    if (d & M_RL) rl_set(r, s, S->want & M_RL);
    if (d & M_MPS) mps_set(r, S->want & M_MPS);
    S->applied = S->want;
}

__attribute__((used)) u32 nvme_passthru(u64 self, u32 nsid, u8 *pkt, u64 ev) {
    init();
    if (ev || !pkt) return PASSTHRU(self, nsid, pkt, ev);                       /* async: untouched */
    apply();
    u8 *cmd = *(u8 **)(pkt + 0x28), *cpl = *(u8 **)(pkt + 0x30);
    u32 opc = cmd ? cmd[0] : 0xffu, q = pkt[0x24];
    if ((S->applied & M_FD) && opc == 0x00 && q == 1 && S->phase && S->more && cpl) {
        for (u32 i = 0; i < 16; i++) cpl[i] = 0;                                /* Flush reported as done */
        S->fd_skipped++;
        return 0;
    }
    u64 t0 = cnt();
    u32 st = PASSTHRU(self, nsid, pkt, ev);
    if ((S->applied & (M_RL | M_MPS)) && opc == 1 && q == 1 &&
        (st || (cpl && (R32(cpl + 12) >> 17)) || cnt() - t0 > S->freq * 2 / 5)) {
        S->bad |= S->applied & (M_RL | M_MPS);                                  /* guard: off until the camera restarts */
        S->want &= ~S->bad; apply();
    }
    return st;
}

/* Pre-capture writer: 1 NEF begin, 7 more frames waiting (arg), 6 NEF done. */
__attribute__((used)) void nvme_mark(u32 code, u32 arg) {
    init();
    if (code == 1) { S->want = fast_on() ? (M_RL | M_MPS | M_FD) & ~S->bad : 0u; S->more = 0; S->phase = 1; }
    else if (code == 7) S->more = arg;
    else if (code == 6) { S->want = 0; S->more = 0; S->phase = 0; }
}

__asm__(".pushsection .text.entry,\"ax\",%progbits\n"
        ".globl nvme_table\n"
        "nvme_table:\n"
        "  b nvme_passthru\n"
        "  ret\n"
        "  ret\n"
        "  ret\n"
        "  b nvme_mark\n"
        "  .word 0x444d564e\n"           /* 'NVMD' */
        ".popsection\n");
