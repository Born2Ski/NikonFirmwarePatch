// UI-only view of RAW recording. Leave the saved shooting-bank value intact.
.text
c_photo:
    movz x8,#0x4254
    movk x8,#0x03d7,lsl #16
    movk x8,#0xa,lsl #32
    ldr w9,[x8]
    cmp w9,#1
    b.ne 1f
    movz x8,#0xc7a4
    movk x8,#0x03d7,lsl #16
    movk x8,#0xa,lsl #32
    ldr w9,[x8]
    cmp w9,#3             // C30
    ccmp w9,#6,#4,ne      // C15, or retain Z=1 for C30
    ccmp w9,#5,#4,ne      // C60, or retain Z=1 for C30/C15
    cset w0,eq
    ret
1:  mov w0,wzr
    ret

.global raw_menu_value
raw_menu_value:
    str x30,[sp,#-16]!
    bl original_403EC398
    cmp w0,#1
    b.ne 1f
    bl c_photo
    cmp w0,#0
    mov w0,#1
    mov w8,#3
    csel w0,w8,w0,ne
1:  ldr x30,[sp],#16
    ret

.global raw_menu_enter
raw_menu_enter:
    str x30,[sp,#-16]!
    bl c_photo
    mov w2,w0
    mov x0,x19
    mov w1,#0x29b6
    bl original_403B1A5C
    mov w0,#0x608
    movk w0,#0x600,lsl #16
    ldr x30,[sp],#16
    b raw_menu_value

.global raw_menu_lossless
raw_menu_lossless:
    str x30,[sp,#-16]!
    bl c_photo
    ldr x30,[sp],#16
    cbnz w0,2f
    mov w0,#0x608
    b original_405E6994
2:  ret

.global raw_menu_star
raw_menu_star:
    str x30,[sp,#-16]!
    bl c_photo
    cbz w0,3f
    mov w0,#0x608
    movk w0,#0x600,lsl #16
    bl original_403EC398
    cmp w0,#1
    b.eq 4f
3:  ldr x30,[sp],#16
    mov w0,#0x608
    b original_405E69A4
4:  ldr x30,[sp],#16
    ret

// Only these two quality/size role records call this predicate. The native
// painter and the input handler both pass the secondary index in w1.
.global raw_menu_size_disabled
raw_menu_size_disabled:
    sub w8,w1,#1
    cmp w8,#1
    b.ls c_photo
    mov w0,wzr
    ret

// Live overlay: substitute L in the UI descriptor, after the bank/area
// selected which cached size to read. Preserve the original property result.
.global raw_menu_size_live
raw_menu_size_live:
    ldrb w10,[x10]
    stp x0,x30,[sp,#-32]!
    stp x8,x9,[sp,#16]
    bl c_photo
    cbz w0,1f
    mov w10,wzr
1:  ldp x8,x9,[sp,#16]
    ldp x0,x30,[sp],#32
    b original_40441108

// Alternate layout: use its native size-index-zero return. Its primary
// quality lookup still uses the ordinary 13-entry menu in C15/C30.
.global raw_menu_size_alt
raw_menu_size_alt:
    str x30,[sp,#-16]!
    bl c_photo
    ldr x30,[sp],#16
    cbnz w0,1f
    mov x0,xzr
    b original_403ACCCC
1:  ret

// RAW extras (HN28): Photo shooting menu row 2 (item 0x2CAA, hidden in stock) opens a page of switches (menu state
// 0x30, free in stock: only hidden rows of other menus list it). The switches live in one spare byte of settings group
// 1Eh (after the one-byte setting 1E50h; saved with the group, not banked): 0x80 | bits once a switch was toggled here.
// Before that the byte holds what the Turbo RAW row (03.12.t1..v11) wrote: 0 never set, 1 Turbo Off, 2 Turbo On; the
// other switches then take their default. The pre-capture unit (firmware.c, extras()), z8relbank, z8dxlens and z8nvme
// decode the same byte. Bits: 0 Turbo RAW, 1 DX lens: FX area, 2 C20, 3 release mode per bank, 4 pre-release per bank,
// 5 Turbo RAW review. Bit 6 (as extras_bits reports it) is Fast card writes (HN29, z8nvme; its row shows only when the
// unit is built in), kept in its own spare byte 0xA03D732A6 (0 never set = On, else 0x80 | on), so a byte written by an
// earlier firmware (bit 6 = 0) does not switch it off; bit 6 of the byte above is ignored (03.12.k1 stored it there).
// Bit 7 is Continue when buffer full (HN35, firmware.c), bit 1 of that same byte set = Off (so every byte an earlier
// firmware wrote reads On).
#ifndef TURBO_DEFAULT
#define TURBO_DEFAULT 0
#endif
#define X_DEFAULT (0x3e | TURBO_DEFAULT)
#define ITEM_BASE 0x4e10        // row items 0x4E10 + bit: above 0x4B98, outside the menu's per-item arrays
#define C15_LABEL 2371          // "C15" (release mode label, every language)
#define C20_LABEL 3253          // "C20" (z8patch.shared raw-extras)

// w0 = the switch bits (bits 6 and 7 from the HN29 byte); uses x8 only.
extras_bits:
    movz x8,#0x32a5
    movk x8,#0x03d7,lsl #16
    movk x8,#0xa,lsl #32
    ldrb w0,[x8]
    tbz w0,#7,1f
    and w0,w0,#0x3f
    b 4f
1:  mov w8,#X_DEFAULT
    cmp w0,#2
    b.ne 2f
    orr w0,w8,#1
    b 4f
2:  cmp w0,#1
    b.ne 3f
    and w0,w8,#0xfffffffe
    b 4f
3:  mov w0,w8
4:  movz x8,#0x32a6                 // HN29 Fast card writes byte
    movk x8,#0x03d7,lsl #16
    movk x8,#0xa,lsl #32
    ldrb w8,[x8]
    tbz w8,#7,5f
    bfi w0,w8,#6,#1                 // bit 6: Fast card writes = byte bit 0
    tbnz w8,#1,6f                   // HN35: byte bit 1 set = Continue when buffer full Off
    orr w0,w0,#0x80
6:  ret
5:  orr w0,w0,#0xc0                 // never set: both On
    ret

// Applies the switches to the camera's own initialized data; returns w0 = the bits. Uses x0 and x8..x9 (leaf after
// extras_bits). C20: the C15 release-mode icon in the three RAM icon lists (2670 = frames symbol with 20, as CH 20 fps;
// stock 2650 with 15). Turbo RAW review: the Auto series playback speed page (state 0x275) lists 5 rows (with Turbo RAW)
// or the stock 4. Called on every string read, from the shooting-display icon hook and after a toggle.
extras_sync:
    str x30,[sp,#-16]!
    bl extras_bits
    ldr x30,[sp],#16
    mov w9,#2650
    tbz w0,#2,1f
    mov w9,#2670
1:  movz x8,#0x5646                 // release-mode icon list 0xa028b5640 [S, CL, CH, C15, ...], entry 3 (u16)
    movk x8,#0x028b,lsl #16
    movk x8,#0xa,lsl #32
    strh w9,[x8]
    movz x8,#0x0698                 // release-mode selection options 0xa02880660, option 3 value (u32)
    movk x8,#0x0288,lsl #16
    movk x8,#0xa,lsl #32
    str w9,[x8]
    movz x8,#0x2c90                 // shooting-display release-mode icons 0xa02872700, code 13 (u32)
    movk x8,#0x0287,lsl #16
    movk x8,#0xa,lsl #32
    str w9,[x8]
    mov w9,#4
    tbz w0,#5,2f
    mov w9,#5
2:  movz x8,#0x95c0                 // speed page record 0xa028c95a0 +0x20: row count (u16)
    movk x8,#0x028c,lsl #16
    movk x8,#0xa,lsl #32
    strh w9,[x8]
    ret

// OK, right and touch on a RAW extras row (the page's shared row table, as the stock switch toggle 0x4051226C):
// the row under the cursor gives the item, item - ITEM_BASE the bit. Flip it, store 0x80 | bits, apply, then redraw the
// row's switch with 0x40512068(ctx, on) as the stock toggle does.
.global extras_toggle
extras_toggle:
    stp x19,x30,[sp,#-16]!
    ldr x19,[x0]
    ldr x9,[x19,#0x50]
    ldrh w10,[x19,#0x58]
    ldrh w11,[x19,#0x32]
    ldr x9,[x9,#0x10]
    add w10,w10,w11
    mov w8,#44
    madd x9,x10,x8,x9
    ldr w9,[x9,#0x18]
    mov w10,#ITEM_BASE
    sub w12,w9,w10
    cmp w12,#8
    b.hs 9f
    bl extras_bits
    mov w10,#1
    lsl w10,w10,w12
    eor w13,w0,w10
    cmp w12,#6
    b.lo 5f
    ubfx w11,w13,#6,#1              // HN29/HN35: their own byte, 0x80 | Fast card writes On | Continue Off << 1
    tst w13,#0x80
    orr w10,w11,#2
    csel w11,w11,w10,ne
    orr w11,w11,#0x80
    movz x8,#0x32a6
    b 6f
5:  and w11,w13,#0x3f
    orr w11,w11,#0x80
    movz x8,#0x32a5
6:  movk x8,#0x03d7,lsl #16
    movk x8,#0xa,lsl #32
    strb w11,[x8]
    bl extras_sync
    lsr w1,w13,w12
    and w1,w1,#1
    mov x0,x19
    ldp x19,x30,[sp],#16
    b original_40512068
9:  ldp x19,x30,[sp],#16
    ret

// State 0x30 refresh callback (x0 = the menu): set each row's switch, as the stock refresh callbacks do
// (0x4050A6F0(menu, item, 0x4BA7) -> node, 0x405121E4(node, on)). The state's own refresh (0x405DB3C4) only serves its
// hidden stock item 0x2ACF and is not called.
.global extras_refresh
extras_refresh:
    stp x29,x30,[sp,#-48]!
    stp x19,x20,[sp,#16]
    str x21,[sp,#32]
    mov x19,x0
    bl extras_sync
    mov w20,w0
    mov w21,wzr
1:  mov w8,#ITEM_BASE
    add w1,w8,w21
    mov w2,#0x4ba7
    mov x0,x19
    bl original_4050A6F0
    cbz x0,2f
    lsr w1,w20,w21
    and w1,w1,#1
    bl original_405121E4
2:  add w21,w21,#1
    cmp w21,#8
    b.lo 1b
    ldr x21,[sp,#32]
    ldp x19,x20,[sp,#16]
    ldp x29,x30,[sp],#48
    ret

// State 0x30's availability callback (4th): always available. Its stock one (0x405DB3A0) asks the disable predicates of
// an unrelated item (32), as state 0x29's own callback does not.
.global extras_available
extras_available:
    mov w0,#1
    ret

// String reader 0x4032E130(language, id, &text, &length), whose first instruction (mov x9,#0xac48) branches here:
// with C20 On the C15 release-mode label reads as string C20_LABEL ("C20"). Also applies the switches (extras_sync).
.global extras_string
extras_string:
    stp x0,x30,[sp,#-16]!
    bl extras_sync
    cmp w1,#C15_LABEL
    b.ne 1f
    tbz w0,#2,1f
    mov w1,#C20_LABEL
1:  ldp x0,x30,[sp],#16
    mov x9,#0xac48
    b original_4032E134

// Shooting display: 0x4041D1A0 (add x8,x8,w9,uxtw #2: x8 = the (outlined, plain) image pair of index w9 from
// 0x42AE792E; the function saved x30) calls here. Index 22 is C15 (2713, 2650); with C20 On its pair reads (2714, 2670),
// the frames symbol with 20 of both sets. After the call only x8 and w0..w4 (set there) are used.
.global extras_pair
extras_pair:
    add x8,x8,w9,uxtw #2
    cmp w9,#22
    b.ne 1f
    stp x8,x30,[sp,#-16]!
    bl extras_sync
    ldp x8,x30,[sp],#16
    tbz w0,#2,1f
    adr x8,c20_pair
1:  ret

// C15 pre-release frames: 0x40F9A508 (C15 case of the per-mode lookup 0x40F9A488, a leaf) branches here from its
// table load (mov x9,#0xa9f0) with w8 = setting - 1 (0..2, checked). Stock table 0xA029CA9F0 = 5, 8, 15 (0.3/0.5/1 s
// at 15 fps); with C20 On 6, 10, 20 (at 20 fps).
.global extras_c15_pre
extras_c15_pre:
    mov w10,w8
    str x30,[sp,#-16]!
    bl extras_bits
    ldr x30,[sp],#16
    adr x9,c20_pre
    tbnz w0,#2,1f
    movz x9,#0xa9f0
    movk x9,#0x029c,lsl #16
    movk x9,#0xa,lsl #32
1:  ldr w0,[x9,w10,uxtw #2]
    ret

.balign 4
c20_pre:
    .word 6, 10, 20
c20_pair:
    .hword 2714, 2670

// Page rows (Fast card writes last: the page lists 7 rows without z8nvme, 8 with it; 44 bytes each, the stock switch row of "DX crop alert": label, no help, switch style 0x20901005 with
// resource 0x1326) and their row-table pointers (all the page's own table 0x43E34940, rewritten by sites.py).
.balign 4
.global extras_rows
extras_rows:
    .word 3250, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 0, 0x40004, 0xffffffff, 0xffffffff, 2   // Turbo RAW
    .word 3256, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 5, 0x40004, 0xffffffff, 0xffffffff, 2   // Turbo RAW review
    .word C20_LABEL, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 2, 0x40004, 0xffffffff, 0xffffffff, 2   // C20
    .word 3252, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 1, 0x40004, 0xffffffff, 0xffffffff, 2   // DX lens: FX area
    .word 3254, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 3, 0x40004, 0xffffffff, 0xffffffff, 2   // Bank: release mode
    .word 3255, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 4, 0x40004, 0xffffffff, 0xffffffff, 2   // Bank: pre-release
    .word 3258, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 7, 0x40004, 0xffffffff, 0xffffffff, 2   // Continue when buffer full (HN35)
    .word 3257, 0xffff, 0xffff, 0, 0x20901005, 0x1326, ITEM_BASE + 6, 0x40004, 0xffffffff, 0xffffffff, 2   // Fast card writes (HN29)
.balign 8
.global extras_events
extras_events:
    .quad 0x43e34940, 0x43e34940, 0x43e34940, 0x43e34940, 0x43e34940, 0x43e34940, 0x43e34940, 0x43e34940
