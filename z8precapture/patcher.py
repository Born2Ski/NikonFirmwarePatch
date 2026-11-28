"""Pre-capture HN11 public adapter (HN13: DX): feature windows only; no identity or loader edits."""
import struct
from z8prores.package import require
BASE=0x40160000

def c20(symbols):
    """HN24 is built into the unit: C15 at 20 fps, its pre-release counts, label and icons."""
    return 'precapture_frame_skip' in symbols


def edits(code, symbols):
    entries = {k: int(v['va'], 16) for k, v in symbols.items()}

    def branch(at, to, tail=False):
        d = to-at
        require(d % 4 == 0 and -(1 << 27) <= d < (1 << 27), 'Branch target out of range')
        return struct.pack('<I', (0x14000000 if tail else 0x94000000) | ((d // 4) & 0x3ffffff))

    def bl(at, to):
        return branch(at, to)

    values = {
        0xe0fe90: bl(0x40f6fe90, entries['precapture_history_entry']),
        0xd4915c: bytes.fromhex('e00317aa') + bl(0x40ea9160, entries['precapture_tdec_release_entry']) + bytes.fromhex('1f2003d5'),
        0xd43638: bl(0x40ea3638, entries['precapture_write_file']),
        0xd4eb60: bl(0x40eaeb60, entries['precapture_main_rc']),
        0xe0ff38: bl(0x40f6ff38, entries['precapture_current_entry']),
        0xee8e1c: bl(0x41048e1c, entries['precapture_y_size_entry']),
        0xd49fac: bl(0x40ea9fac, entries['precapture_y_alloc_entry']),
        0xd4eeec: bl(0x40eaeeec, entries['precapture_main_step']),
        0xd4ef10: bl(0x40eaef10, entries['precapture_main_step']),
        0x4d2ffc0: struct.pack('<I', 0x1082600),
        0x4d2ffc8: struct.pack('<I', 0x70c200),     # HN23: C60's E request (stock 0x70c000) + the record
        0x4d2ffcc: struct.pack('<I', 0x1082600),
        0x890000: code,
    }
    # HN13 Z: first instruction of the HSFC mode normaliser 0x41059c60 (cmp w0,#6) -> b precapture_area_mode
    values[0x41059c60 - 0x40160000] = branch(0x41059c60, entries['precapture_area_mode'], tail=True)
    for at, entry in (
        (0x40e99798, 'precapture_tenc_config'),
        (0x4104df14, 'precapture_e_alloc'),
        (0x40e997c8, 'precapture_e_size'),
        (0x40f98c4c, 'precapture_e_size'),
        (0x40f9a0b4, 'precapture_e_size'),
        (0x40ea9048, 'precapture_tdec_sel_entry'),
        (0x40e8904c, 'precapture_dec_job'),      # HN18: decode job builder call
        (0x40eaa4ec, 'precapture_dev_run_entry'),  # HN21: synchronous development job call in 0x40eaa498
        (0x403acce8, 'precapture_gui_mode'),
        (0x40f96c90, 'precapture_ready_margin'),
        (0x40d49044, 'precapture_ui_mode'),
        (0x40d424f0, 'precapture_ui_mode'),
    ):
        values[at - 0x40160000] = bl(at, entries[entry])
    if c20(symbols):                               # HN24 (C15 at 20 fps) only when the unit carries the frame selector
        # HN28: the C15 pre-release frames (6/10/20 for 0.3/0.5/1 s, stock 5/8/15) follow the C20 switch at runtime
        # (menu unit, extras_c15_pre), so the stock table at 0x4cd59f0 stays.
        # photo-frame selector calls: pre-capture (sequence state 2) and the burst (state 3, HN35's no-room skip first)
        values[0x40f807bc - 0x40160000] = bl(0x40f807bc, entries['precapture_frame_skip'])
        values[0x40f80a2c - 0x40160000] = bl(0x40f80a2c, entries['precapture_burst_frame'])
    # HN35 K: the burst's free-frame read (bl 0x40f97a7c, its only call) in the stop test of state 3 (0x40f80608)
    require(code is not None and 'precapture_burst_room' in entries, 'Pre-capture unit lacks HN35')
    values[0x40f80608 - 0x40160000] = bl(0x40f80608, entries['precapture_burst_room'])
    # HN35 Q: the stop test's reads of flags 0x55 (no free frame in pool 0x39) and 0x56 (blr x8, w0 = the flag)
    for at in (0x40f80668, 0x40f8067c):
        values[at - 0x40160000] = bl(at, entries['precapture_burst_flag_entry'])
    for at in (0x40ec4640, 0x40ec6a8c, 0x40f24e08, 0x41014b1c, 0x410e71f8):
        values[at - 0x40160000] = branch(at, entries['precapture_cap_update'], tail=at == 0x40ec4640)
    # These are callback pointers in the initialized-data image, not AArch64 branches.
    callbacks = {93: 'precapture_display_mode', 112: 'precapture_quality_code',
                 113: 'precapture_quality_code', 114: 'precapture_ordinary_code',
                 115: 'precapture_ordinary_code', 116: 'precapture_quality_star',
                 117: 'precapture_ordinary_star', 129: 'precapture_display_mode',
                 130: 'precapture_display_mode'}
    for index, entry in callbacks.items():
        at = 0x4b13000 + 0xa0295c558 + 0x68 * index + 0x30 - 0xa02808000
        values[at] = struct.pack('<Q', entries[entry])
    # HN21: the second full-size pass in the C15/C30 pipeline's stage list (initialized-data image), stock 0x40eaafc0
    values[0x44f385a0 - 0x40160000] = struct.pack('<Q', entries['precapture_pass2_step'])
    values[0x704938] = bl(0x40864938,entries['precapture_expand'])
    values[0x7103E4] = bl(0x408703E4,entries['precapture_dcf_item'])
    ids=entries['precapture_dcf_ids']
    require(0x409F0000<=ids<0x40A00000 and ids%4==0,'Pre-capture subscription table')
    require(code[ids-0x409F0000:ids-0x409F0000+36]==struct.pack('<9I',0x601,0x2000688,0x6000689,0x200172A,0x2000600,0x6000604,0x6000608,0x6000605,0x6000606),'Pre-capture subscription contents')
    values[0x70E908]=struct.pack('<I',0xD2800002|((ids&65535)<<5))
    values[0x70E918]=struct.pack('<I',0xF2A00002|((ids>>16)<<5))
    values[0x70E94C]=struct.pack('<I',0x52800003|(9<<5))
    return [dict(offset=at,new=raw,purpose='pre-capture code' if at==0x890000 else 'pre-capture hook/data '+hex(at)) for at,raw in sorted(values.items())]


# HN24: C15 takes 20 photos per second, so its release-mode label (UI string 2371, "C15" in every language; Arabic has
# a right-to-left mark in front) reads "C20" and its icons show 20. HN28: all of it follows the RAW extras switch C20 at
# runtime (z8precapture/menu/hooks.S): the label through the string reader (string 3253 "C20"), the shooting-display
# pair through its reader, the three RAM icon references below written by extras_sync. The image keeps the stock
# values; c20_checks() makes sure they are the ones the menu unit expects.
C15_LABEL = 2371
ICON_15 = 2650      # PNG table 0x431d96d0 index: frames symbol with 15 (64x32 set); 2670 = with 20 (CH 20 fps)
# (EG offset, format, record {index, kind 1 = image} before the value or None, where)
ICONS = (
    (0x4BC0646, '<H', None, 'release-mode icon list RAM 0xa028b5640 [S, CL, CH, C15, C30, C60, C120], entry 3'),
    (0x4B8B698, '<I', (3, 1), 'release-mode selection options RAM 0xa02880660, option 3'),
    (0x4B7DC90, '<I', (13, 1), 'shooting-display release-mode icons RAM 0xa02872700, code 13'),
)
# The shooting display draws the high-speed modes from (outlined 68x36, plain 64x32) image pairs [C15, C30, C60, C120] at
# VA 0x42ae7984 (read-only data, read only by 0x4041d18c..: base 0x42ae792e, index 22 = C15).
PAIRS = 0x2987986                                               # EG offset of C15's pair
PAIRS_STOCK = (2713, 2650, 2708, 2643, 5929, 5930, 2709, 2644)   # C15, C30, C60, C120 (outlined, plain)


def c20_checks(eg):
    for off, fmt, ident, why in ICONS:
        require(eg[off - 8:off] == struct.pack('<2I', *ident) if ident else True, f'C15 icon: unexpected record at {off:#x}')
        require(struct.unpack_from(fmt, eg, off)[0] == ICON_15, f'C15 icon: unexpected stock image at {off:#x} ({why})')
    require(struct.unpack_from('<8H', eg, PAIRS) == PAIRS_STOCK, 'C15 icon: unexpected shooting-display pair table')
    require(struct.unpack_from('<3I', eg, 0x4CD59F0) == (5, 8, 15), 'C15 pre-release: unexpected stock table')


# HN27: Turbo RAW review, a fifth row on the Auto series playback speed page (state 0x275) and the playback hooks.
SPEED_PAGE = 0x4BD45A0               # EG offset of the page record (initialized data, RAM 0xa028c95a0): +0x10 rows, events, count
SPEED_ROWS, SPEED_EVENTS, SPEED_TABLE = 0x43D405AC, 0x43D40660, 0x43D53E88
SPEED_ENTRY_CB = 0x4BF7A48           # EG offset of state 0x275's callbacks (RAM 0xa028eca48) +0: entry 0x4059325c
SPEED_ACTION = 0x405932D4            # OK/right/touch action of the speed rows in their shared table
SPEED_ACTION_EVENTS = (0x286, 0x28B, 0x2AE)


def review_edits(eg, code, symbols):
    entries = {k: int(v['va'], 16) for k, v in symbols.items()}

    def branch(at, to, tail=False):
        d = to - at
        require(d % 4 == 0 and -(1 << 27) <= d < (1 << 27), 'Branch target out of range')
        return struct.pack('<I', (0x14000000 if tail else 0x94000000) | ((d // 4) & 0x3ffffff))

    rows, events = entries['precapture_review_rows'], entries['precapture_review_events']
    blob = code[rows - 0x409F0000:rows - 0x409F0000 + 5 * 44]
    require(blob[:4 * 44] == eg[SPEED_ROWS - BASE:SPEED_ROWS - BASE + 4 * 44], 'Turbo RAW review: stock speed rows differ')
    require(struct.unpack_from('<11I', blob, 4 * 44)[6] == 0x4E08 and
            struct.unpack_from('<5Q', code, events - 0x409F0000) == (SPEED_TABLE,) * 5 and
            struct.unpack_from('<4Q', eg, SPEED_EVENTS - BASE) == (SPEED_TABLE,) * 4, 'Turbo RAW review: row data')
    out = [dict(offset=SPEED_PAGE + 0x10, old=struct.pack('<QQH', SPEED_ROWS, SPEED_EVENTS, 4),
                new=struct.pack('<QQH', rows, events, 5), purpose='pre-capture HN27: speed page rows (+ Turbo RAW), count 5'),
           dict(offset=SPEED_ENTRY_CB, old=struct.pack('<Q', 0x4059325C), new=struct.pack('<Q', entries['precapture_review_entry']),
                purpose='pre-capture HN27: speed page entry callback')]
    seen = []
    for k in range(32):
        at = SPEED_TABLE - BASE + 32 * k
        event, action = struct.unpack_from('<2Q', eg, at)
        if event == 0x3BB:
            break
        if action == SPEED_ACTION:
            seen.append(event)
            out.append(dict(offset=at + 8, old=struct.pack('<Q', SPEED_ACTION), new=struct.pack('<Q', entries['precapture_review_action']),
                            purpose=f'pre-capture HN27: speed row action (event {event:#x})'))
    require(tuple(seen) == SPEED_ACTION_EVENTS, 'Turbo RAW review: unexpected speed row transitions')
    for at, old_to, entry, tail, why in (
            (0x40593184, 0x403F645C, 'precapture_review_icon', True, 'speed value icon in the options page refresh'),
            (0x40632310, 0x4061C658, 'precapture_review_advance', True, 'image move in the auto playback tick (usual branch)'),
            (0x406339D0, 0x4061C658, 'precapture_button_step', True, 'image move of the series playback button (HN34)'),
            (0x4061C898, 0x4063E348, 'precapture_review_interval', False, 'auto playback start interval'),
            (0x406322DC, 0x4063E348, 'precapture_review_interval', False, 'auto playback tick interval')):
        out.append(dict(offset=at - BASE, old=branch(at, old_to, tail), new=branch(at, entries[entry], tail),
                        purpose='pre-capture HN27: ' + why))
    for e in out:
        require(eg[e['offset']:e['offset'] + len(e['old'])] == e['old'], f"Turbo RAW review: unexpected stock bytes at {e['offset']:#x}")
    return out
