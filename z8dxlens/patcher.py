"""FX image area with DX lenses (upstream issue #45): fixed byte edits only, no code cave.

Stock C3.11 forces DX whenever an electronic DX lens is attached: lens kind 0x04002d0c in {1 Z, 3 F/FTZ}
and lens-covers-FX 0x04002d13 == 0.  These edits make the image-area logic treat such a lens like an FX
lens, so the user's own image-area choice is used.  The camera no longer switches to DX by itself; the
user selects DX when wanted.  The lens is still reported truthfully (PTP LensType DX bit, EXIF), and
Image Dust Off ref photo stays unavailable with DX lenses (UI predicate #38 is left intact).
"""
import struct
from z8prores.package import require

BASE = 0x40160000
B_ALWAYS = 0x14000000
NOP = 0xd503201f


def _b(at, to):
    return B_ALWAYS | (((to - at) // 4) & 0x3ffffff)


# (VA, stock word, new word, purpose)
CODE = (
    (0x40ed91c0, 0x35000069, _b(0x40ed91c0, 0x40ed91cc),
     'image-area resolver keeps the chosen area with a DX lens (cbnz w9 -> b)'),
    (0x40ed9174, 0x35fffe69, _b(0x40ed9174, 0x40ed9140),
     'image-area resolver, video at 120p/100p and slow motion: no DX crop for a DX lens (cbnz w9 -> b)'),
    (0x40ed8f9c, 0x0a080128, 0x2a1f03e8,
     'video frame-size helper treats a DX lens as FX (and w8,w9,w8 -> mov w8,wzr)'),
    (0x4067c478, 0x340000c0, _b(0x4067c478, 0x4067c490),
     'button command 0x95 not blocked by a DX lens'),
    (0x405e0560, 0x350000a0, _b(0x405e0560, 0x405e0574),
     'image-area button event not ignored with a DX lens'),
    (0x4081c728, 0x34000200, NOP, 'PTP photo image-area set allowed with a DX lens'),
    (0x4081cde4, 0x34000160, NOP, 'PTP video image-area set allowed with a DX lens'),
    (0x4083ffd4, 0x34000120, NOP, 'PTP movie frame-size set allowed with a DX lens'),
)

# UI disable lists: table 0x42dedf78, 16-byte entries {u64 list, u16 count}; predicate 38 = DX lens attached.
TABLE = 0x42dedf78
PRED_DX = 38
# Multi-predicate lists: replace 38 with a predicate already present in the same list.
LIST_SLOTS = (
    (25, 1, 7, 'photo Choose image area row'),
    (430, 1, 7, 'photo image-area button function'),
    (107, 1, 97, 'video Choose image area row'),
    (459, 2, 97, 'video image-area button function'),
)
# Single-predicate lists (38,): count -> 0.
COUNT_ITEMS = ((82, 'time-lapse movie Choose image area'),) + tuple(
    (i, 'FX-only video frame size option') for i in range(109, 132))


def edits(eg):
    out = []

    def add(va, old, new, why):
        o = va - BASE
        require(eg[o:o + len(old)] == old, f'dx-lens-fx: unexpected stock bytes at {va:#x}')
        out.append(dict(offset=o, old=old, new=new, purpose='dx-lens-fx: ' + why))

    for va, old, new, why in CODE:
        add(va, struct.pack('<I', old), struct.pack('<I', new), why)

    def entry(item):
        ptr, count = struct.unpack_from('<QH', eg, TABLE - BASE + 16 * item)
        return ptr, count

    for item, slot, repl, why in LIST_SLOTS:
        ptr, count = entry(item)
        lst = struct.unpack_from(f'<{count}I', eg, ptr - BASE)
        require(lst[slot] == PRED_DX and repl in lst and lst.count(PRED_DX) == 1,
                f'dx-lens-fx: item {item} list layout')
        add(ptr + 4 * slot, struct.pack('<I', PRED_DX), struct.pack('<I', repl),
            f'UI item {item} ({why}) not greyed by a DX lens')

    for item, why in COUNT_ITEMS:
        ptr, count = entry(item)
        require(count == 1 and struct.unpack_from('<I', eg, ptr - BASE)[0] == PRED_DX,
                f'dx-lens-fx: item {item} list layout')
        add(TABLE + 16 * item + 8, struct.pack('<H', 1), struct.pack('<H', 0),
            f'UI item {item} ({why}) not greyed by a DX lens')
    return out


# ---- Runtime switch (RAW extras, z8precapture/menu): the same behaviour, chosen by bit 1 of the RAW extras byte ----
# The eight code sites branch to stubs that load the byte (x16, saved on the stack with x17) and either do what the
# fixed edit does or execute the stock instruction; neither path touches the condition flags. The five readers of
# the UI disable-list table (mov x8,#0xdf78; movk x8,#0x42de,lsl #16; movk #0,lsl #32; movk #0,lsl #48) branch to
# stubs that set x8 to the stock table or to a copy with the fixed edits' 28 list changes, then return after the four
# instructions. A value without bit 7 (never toggled, or the Turbo RAW row's 1/2) means the default: On.
RUNTIME_AT, RUNTIME_END = 0x409FC000, 0x409FF000   # free tail of the pre-capture unit's window, below the RAW menu unit
EXTRAS, DX_BIT = 0xA03D732A5, 1
READERS = (0x403A0390, 0x403A1674, 0x403A35E8, 0x403D581C, 0x4056A0C0)   # mov x8,#0xdf78 of each table reader
TABLE_ENTRIES = 489                                 # items 0..0x1E8 (the first reader rejects items above 0x1E8)
READER_WORDS = (0xD29BEF08, 0xF2A85BC8, 0xF2C00008, 0xF2E00008)


def _cond_target(at, word):
    """cbz/cbnz wN target and register of a stock word."""
    require(word & 0x7E000000 == 0x34000000 and not word >> 31, f'dx-lens-fx: no cbz/cbnz at {at:#x}')
    imm = (word >> 5) & 0x7FFFF
    if imm & 0x40000:
        imm -= 1 << 19
    return at + 4 * imm, word & 31, bool(word & 0x01000000)


def runtime(eg):
    """(module bytes at RUNTIME_AT, site edits) for the switchable form."""
    from z8prores.a64 import Block
    b = Block(RUNTIME_AT)

    def tbnz(rt, bit, target):
        b._rel(lambda pc: 0x37000000 | bit << 19 | (((b._target(target) - pc) >> 2) & 0x3FFF) << 5 | rt)

    def dx_on(reg, on_label):           # ldrb wR of the byte; default (no bit 7) or bit 1 -> on_label
        b.mov_x64(reg, EXTRAS)
        b.ldrb_w(reg, reg)
        b.tbz_w(reg, 7, on_label)
        tbnz(reg, DX_BIT, on_label)

    sites = []
    for k, (va, stock, new, why) in enumerate(CODE):
        require(struct.unpack_from('<I', eg, va - BASE)[0] == stock, f'dx-lens-fx: unexpected stock word at {va:#x}')
        b.label(f'code{k}')
        b.stp_pre(16, 17, -16)
        dx_on(16, f'on{k}')
        b.ldp_post(16, 17, 16)
        if stock & 0x7E000000 == 0x34000000:        # cbz/cbnz: off = the stock test, on = the fixed edit
            target, reg, nonzero = _cond_target(va, stock)
            (b.cbnz_w if nonzero else b.cbz_w)(reg, f'taken{k}')
            b.b(va + 4)
            b.label(f'taken{k}')
            b.b(target)
            b.label(f'on{k}')
            b.ldp_post(16, 17, 16)
            if new == NOP:
                b.b(va + 4)
            else:
                require(new == _b(va, target), f'dx-lens-fx: fixed edit at {va:#x} is not the stock branch made unconditional')
                b.b(target)
        else:                                       # and w8,w9,w8 -> mov w8,wzr
            b.raw(stock)
            b.b(va + 4)
            b.label(f'on{k}')
            b.ldp_post(16, 17, 16)
            b.raw(new)
            b.b(va + 4)
        sites.append((va, stock, f'code{k}', 'switchable: ' + why))
    for k, va in enumerate(READERS):
        require(struct.unpack_from('<4I', eg, va - BASE) == READER_WORDS, f'dx-lens-fx: unexpected table reader at {va:#x}')
        b.label(f'reader{k}')
        dx_on(8, f'copy{k}')
        b.raw(READER_WORDS[0])
        b.raw(READER_WORDS[1])
        b.b(va + 16)
        b.label(f'copy{k}')
        b.raw(0xD2800008)                          # movz x8,#lo(table): patched below
        b.raw(0xF2A00008)                          # movk x8,#hi(table),lsl #16
        b.b(va + 16)
        sites.append((va, READER_WORDS[0], f'reader{k}', 'UI disable-list table: stock or the DX-lens copy'))
    code = bytearray(b.bytes())
    # Lists (the fixed edits' list changes) and the table copy after the code.
    data_at = (RUNTIME_AT + len(code) + 15) & ~15
    table = bytearray(eg[TABLE - BASE:TABLE - BASE + 16 * TABLE_ENTRIES])
    lists = bytearray()
    for item, slot, repl, why in LIST_SLOTS:
        ptr, count = struct.unpack_from('<QH', table, 16 * item)
        lst = list(struct.unpack_from(f'<{count}I', eg, ptr - BASE))
        require(lst[slot] == PRED_DX and repl in lst and lst.count(PRED_DX) == 1, f'dx-lens-fx: item {item} list layout')
        lst[slot] = repl
        struct.pack_into('<Q', table, 16 * item, data_at + len(lists))
        lists += struct.pack(f'<{count}I', *lst)
    for item, why in COUNT_ITEMS:
        ptr, count = struct.unpack_from('<QH', table, 16 * item)
        require(count == 1 and struct.unpack_from('<I', eg, ptr - BASE)[0] == PRED_DX, f'dx-lens-fx: item {item} list layout')
        struct.pack_into('<H', table, 16 * item + 8, 0)
    table_at = (data_at + len(lists) + 15) & ~15
    require(table_at < 1 << 32, 'dx-lens-fx: table copy above 4 GiB')
    labels = b.labels
    for k in range(len(READERS)):                   # copy{k}: movz x8,#lo(table); movk x8,#hi(table),lsl #16
        o = labels[f'copy{k}'] - RUNTIME_AT
        struct.pack_into('<2I', code, o, 0xD2800008 | (table_at & 0xFFFF) << 5, 0xF2A00008 | (table_at >> 16) << 5)
    blob = bytes(code) + bytes(data_at - RUNTIME_AT - len(code)) + bytes(lists)
    blob += bytes(table_at - RUNTIME_AT - len(blob)) + bytes(table)
    require(RUNTIME_AT + len(blob) <= RUNTIME_END, 'dx-lens-fx: runtime module exceeds its window')
    out = [dict(offset=RUNTIME_AT - BASE, old=bytes(len(blob)), new=blob,
                purpose=f'dx-lens-fx: switchable code ({len(code)} bytes) and DX-lens copy of the disable-list table at {table_at:#x}')]
    for va, stock, label, why in sites:
        require(struct.unpack_from('<I', eg, va - BASE)[0] == stock, f'dx-lens-fx: unexpected stock word at {va:#x}')
        out.append(dict(offset=va - BASE, old=struct.pack('<I', stock), new=struct.pack('<I', _b(va, labels[label])),
                        purpose='dx-lens-fx: ' + why))
    return out
