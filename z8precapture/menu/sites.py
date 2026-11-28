"""Factory C 3.11 photo menu call sites and their displaced instructions."""
import struct
from z8prores.package import require

BASE = 0x409FF000   # the last 4 KiB of the pre-capture cave; the pre-capture unit may use 0x409F0000..0x409FF000
SITES = (
    (0x4049D674, 'raw_menu_size_alt', True, 0x403ACCCC),
    (0x405D9B40, 'raw_menu_value', True, 0x403EC398),
    (0x405DB6CC, 'raw_menu_enter', True, 0x403EC398),
    (0x405E6990, 'raw_menu_lossless', False, None),
    (0x405E69A0, 'raw_menu_star', False, None),
)
MENU = 'pre-capture RAW recording menu'

# RAW extras (HN28): Photo shooting menu row 2 (item 0x2CAA), one of the two rows the stock entry callback hides, opens
# menu state 0x30 (free in stock: its rows are hidden "Disable" rows and nothing transitions to it) as a page of six
# switch rows (hooks.S: extras_rows, extras_toggle, extras_refresh). Every record changed here is referenced only by
# state 0x30 (its page, layout, callbacks and first row table).
EXTRAS = 'pre-capture RAW extras menu'
EXTRAS_STRINGS = (3250, 9)          # z8patch.shared.STRING_IDS['raw-extras']: Turbo RAW, RAW extras, DX lens: FX area,
                                    # C20, Bank: release mode, Bank: pre-release, Turbo RAW review, Fast card writes,
                                    # Continue when buffer full (HN35)
TITLE, C20_LABEL, C15_LABEL = 3251, 3253, 2371
PHOTO_ROWS, EXTRAS_ROW, PLAIN_ROW = 0x43DCF790, 2, 46   # row 46: Auto capture, a no-value row (pixel shift's row 45 too)
ROW_STOCK = (0x43A, 0xFFFF, 0xFFFF, 0, 0x101041, 0xB44, 0x2CAA, 0x40004, 0xFFFFFFFF, 0xFFFFFFFF, 2)
PLAIN_STOCK = (0x702, 0xA3C, 0x702, 0, 0x101040, 0xFFFF, 0x2D0D, 0x40004, 0xFFFFFFFF, 0xFFFFFFFF, 2)
ROW_EVENTS = 0x43E094A0                            # row 2's own transition table (photo page pointer 2)
STAY, BACK, GO, PAGE_STATE = 0x68C, 0x68D, 0x403B1BA8, 0x30
EXTRAS_EVENTS = {                                  # stock entry -> as row 45's (a row that opens a page)
    (0x285, 0x403B1BA4, 0, 0x1): (0x285, 0x403B1BA4, 0, BACK),
    (0x286, GO, 0, 0x1D): (0x286, GO, 0, PAGE_STATE),
    (0x29F, GO, 0x403B1C64, 0x1D): (0x29F, GO, 0x403B1C64, PAGE_STATE),
    (0x2A0, 0x403B1BA4, 0x403B1C64, 0x1): (0x2A0, 0x403B1BA4, 0x403B1C64, BACK),
    (0x2AE, GO, 0, 0x1D): (0x2AE, GO, 0, PAGE_STATE),
    (0x3F, 0x405E2AD8, 0, STAY): (0x28B, GO, 0, PAGE_STATE),   # right (row 2 has none in stock)
}
# The photo menu entry callback 405D9704 hides the items of the list at 42B27788 (2CAAh, 2C13h, 1Ah, ...), count 2.
# Pixel shift (still-photo-tools) sets the count to 1 to show 2C13h; this group moves the list start instead:
# alone 42B2778C (2C13h, 1Ah: hides only 2C13h), with pixel shift 42B27784 (89h, not a photo menu item: hides nothing).
HIDE_LIST, HIDE_STOCK = 0x405D9704, 0xD28EF101    # movz x1,#0x7788
STATES, INIT_EG, INIT_VA = 0x4BFFCC0, 0x4B13000, 0xA02808000
PAGE_30, PAGE_29 = 0xA028CCBB0, 0xA028CC980        # page records (initialized data)
LAYOUT_30, LAYOUT_29 = 0x43DD37F0, 0x43DD27C0      # 3 resources each (68 bytes), title = resource 1 word 0
CALLBACKS_30, AVAILABLE_30, REFRESH_30 = 0xA028E6D28, 0x405DB3A0, 0x405DB3C4  # 5 callbacks: 4th availability, 5th refresh
TABLE_30, SWITCH_TABLE, SWITCH_ACTION = 0x43E34940, 0x43E304E0, 0x4051226C   # 16 entries each; DX crop alert's
# C20 (HN24) at runtime: hooks.S extras_string / extras_pair / extras_c15_pre; (VA, stock word, entry, link)
C20_SITES = (
    (0x4032E130, 0xD2958909, 'extras_string', False),   # string reader: mov x9,#0xac48
    (0x4041D1A0, 0x8B294908, 'extras_pair', True),      # shooting display pair: add x8,x8,w9,uxtw #2
    (0x40F9A514, 0xD2953E09, 'extras_c15_pre', False),  # C15 pre-release frames: mov x9,#0xa9f0
)
EXTRAS_TEXT = {     # labels only (no help text): the shared text area is small with every group selected
    'en': ('Turbo RAW', 'RAW extras', 'DX lens: FX area', None, 'Bank: release mode', 'Bank: pre-release',
           'Turbo RAW review', 'Fast card writes', 'Continue when buffer full'),
    'zh-CN': ('Turbo RAW', 'RAW extras', 'DX 镜头：FX 区域', None, '拍摄菜单库：释放模式', '拍摄菜单库：预拍选项',
              'Turbo RAW 播放', '存储卡快速写入', '缓冲区满时继续拍摄'),   # Chinese translated by AI from the English, with the camera's own terms
    'zh-TW': ('Turbo RAW', 'RAW extras', 'DX 鏡頭：FX 區域', None, '拍攝選單庫：快門釋放模式', '拍攝選單庫：預先釋放捕捉',
              'Turbo RAW 播放', '記憶卡快速寫入', '緩衝區滿時繼續拍攝'),
}
LANGUAGES, TABLE_DIR, BLOB_DIR, FAMILY_STRING, STOCK_ENTRIES = 36, 0x311C5A0, 0x387AF58, 2222, 3137


def init_offset(va):
    return va - INIT_VA + INIT_EG


def extras_strings(eg):
    """The nine strings (eight labels and the title) for each of the 36 languages. The family (en, zh-CN, zh-TW) follows each language's stock
    "Pixel shift shooting" string, as pixel shift's own menu text does, and every glyph must occur in that language's
    stock strings. C20 is the language's own C15 release-mode label with 20 for 15 (Arabic keeps its right-to-left
    mark)."""
    out = []
    B = 0x40160000
    for k in range(LANGUAGES):
        table = struct.unpack_from('<Q', eg, TABLE_DIR + 8 * k)[0] - B
        blob = struct.unpack_from('<Q', eg, BLOB_DIR + 8 * k)[0] - B
        offsets = struct.unpack_from(f'<{STOCK_ENTRIES}i', eg, table)
        text = lambda i: eg[blob + offsets[i]:blob + offsets[i + 1]].decode('utf-16le')
        family = text(FAMILY_STRING)
        texts = list(EXTRAS_TEXT['zh-TW' if '像素' in family and '攝' in family else 'zh-CN' if '像素' in family else 'en'])
        c15 = text(C15_LABEL)
        require(c15.lstrip('\u202b') == 'C15', ('RAW extras: unexpected C15 label of language', k, c15))
        texts[3] = c15.replace('C15', 'C20')
        pool = set(eg[blob + offsets[0]:blob + offsets[STOCK_ENTRIES - 1]].decode('utf-16le', 'replace'))
        missing = sorted({c for c in ''.join(texts) if c != ' ' and c not in pool})
        require(not missing, ('RAW extras: glyphs absent from the stock strings of language', k, missing))
        out.append(texts)
    return out


def apply(image, code, entries, photo=False, fast=False):
    B = 0x40160000
    def branch(site,to,link):
        delta=to-site
        if delta%4 or not -(1<<27)<=delta<1<<27:raise ValueError('Invalid menu branch')
        return struct.pack('<I',(0x94000000 if link else 0x14000000)|((delta//4)&0x3ffffff))
    if BASE+len(code)>0x40A00000 or any(image[BASE-B:BASE-B+len(code)]):
        raise ValueError('RAW menu allocation is occupied')
    yield BASE,bytes(len(code)),code,MENU
    for site,name,link,original in SITES:
        old = branch(site,original,link) if original else bytes.fromhex('00c18052')
        if image[site-B:site-B+4]!=old: raise ValueError(f'Unexpected RAW menu bytes at {site:#x}')
        yield site,old,branch(site,entries[name],link),MENU

    # The source-bank byte is read into w10 inside the live descriptor builder.
    # Each ordinary quality role has five callbacks; replace only callback 4
    # (secondary disabled), leaving the other roles sharing its stub untouched.
    for site, old, new in (
        (0x40441104, bytes.fromhex('4a014039'), branch(0x40441104, entries['raw_menu_size_live'], False)),
        (0x42AEA178, struct.pack('<Q', 0x4043EBA0), struct.pack('<Q', entries['raw_menu_size_disabled'])),
        (0x42AF6460, struct.pack('<Q', 0x4049B9B8), struct.pack('<Q', entries['raw_menu_size_disabled'])),
    ):
        if image[site-B:site-B+len(old)] != old:
            raise ValueError(f'Unexpected quality/size role bytes at {site:#x}')
        yield site, old, new, MENU

    # Row 2: "RAW extras", no help, the no-value style of row 46, item 0x2CAA kept.
    at = PHOTO_ROWS + 44 * EXTRAS_ROW
    require(struct.unpack_from('<11I', image, at - B) == ROW_STOCK, 'RAW extras: unexpected photo menu row 2')
    require(struct.unpack_from('<11I', image, PHOTO_ROWS + 44 * PLAIN_ROW - B) == PLAIN_STOCK, 'RAW extras: unexpected row 46')
    row = list(ROW_STOCK)
    row[0], row[1], row[2] = TITLE, 0xFFFF, TITLE
    row[4], row[5] = PLAIN_STOCK[4], PLAIN_STOCK[5]
    yield at, struct.pack('<11I', *ROW_STOCK), struct.pack('<11I', *row), EXTRAS + ': row 2 (item 0x2CAA) label, no value column'
    # Row 2's transitions: OK, right and touch open state 0x30, left goes back (as row 45's table).
    seen = set()
    for k in range(128):
        entry = struct.unpack_from('<4Q', image, ROW_EVENTS - B + 32 * k)
        if entry[0] == 0x3BB:
            break
        if entry in EXTRAS_EVENTS:
            new = EXTRAS_EVENTS[entry]
            seen.add(entry)
            yield ROW_EVENTS + 32 * k, struct.pack('<4Q', *entry), struct.pack('<4Q', *new), \
                EXTRAS + f': row 2 transition {entry[0]:#x} -> {new[0]:#x} state {new[3]:#x}'
    require(seen == set(EXTRAS_EVENTS), 'RAW extras: unexpected row 2 transitions')
    # Show row 2: move the hidden-item list start (see HIDE_LIST).
    old = struct.pack('<I', HIDE_STOCK)
    require(image[HIDE_LIST - B:HIDE_LIST - B + 4] == old, 'RAW extras: unexpected photo menu entry callback')
    start = 0x7784 if photo else 0x778C
    yield HIDE_LIST, old, struct.pack('<I', 0xD2800001 | (start << 5)), \
        EXTRAS + (': hidden-item list from 42B27784 (pixel shift shows 2C13h)' if photo else ': hidden-item list from 42B2778C (only 2C13h)')

    # State 0x30: its page record becomes state 0x29's ("Choose image area": settings page, list rectangles, footer)
    # with state 0x30's layout, the rows of hooks.S and their row-table pointers: seven (with Continue when buffer full,
    # HN35), or eight with Fast card writes (HN29, only when z8nvme is built in: photo/RAW selections).
    state = struct.unpack_from('<12Q', image, STATES + 96 * PAGE_STATE)
    require(state[5] == CALLBACKS_30 and state[10] == PAGE_30, 'RAW extras: unexpected state 0x30')
    page30 = image[init_offset(PAGE_30):init_offset(PAGE_30) + 0x50]
    page29 = image[init_offset(PAGE_29):init_offset(PAGE_29) + 0x50]
    require(struct.unpack_from('<4Q', page30) == (0x80001002, LAYOUT_30, 0x43DD3900, 0x43DD3958) and
            struct.unpack_from('<H', page30, 0x20)[0] == 2 and
            struct.unpack_from('<4Q', page29) == (0x80001000, LAYOUT_29, 0x43DD28D0, 0x43DD2928), 'RAW extras: page records')
    page = bytearray(page29)
    struct.pack_into('<3Q', page, 8, LAYOUT_30, entries['extras_rows'], entries['extras_events'])
    rows = 8 if fast else 7
    struct.pack_into('<H', page, 0x20, rows)
    yield PAGE_30 - INIT_VA + INIT_EG + B, bytes(page30), bytes(page), EXTRAS + f': state 0x30 page record ({rows} switch rows)'
    # Layout: state 0x29's three resources, title "RAW extras".
    lay30 = image[LAYOUT_30 - B:LAYOUT_30 - B + 4 * 68]
    lay29 = image[LAYOUT_29 - B:LAYOUT_29 - B + 4 * 68]
    require(lay30[3 * 68:] == bytes(68) and lay29[3 * 68:] == bytes(68) and
            struct.unpack_from('<I', lay30, 68)[0] == 0x300, 'RAW extras: layouts')
    lay = bytearray(lay29[:3 * 68])
    struct.pack_into('<I', lay, 68, TITLE)
    yield LAYOUT_30, lay30[:3 * 68], bytes(lay), EXTRAS + ': state 0x30 layout (state 0x29\'s, title RAW extras)'
    # Availability (always) and refresh (the switches) callbacks.
    at = CALLBACKS_30 + 0x18
    old = struct.pack('<2Q', AVAILABLE_30, REFRESH_30)
    require(image[init_offset(at):init_offset(at) + 16] == old, 'RAW extras: state 0x30 callbacks')
    yield at - INIT_VA + INIT_EG + B, old, struct.pack('<2Q', entries['extras_available'], entries['extras_refresh']), \
        EXTRAS + ': state 0x30 availability (always) and refresh callbacks'
    # Row table: the DX crop alert switch table with its toggle replaced by extras_toggle (same 16 entries).
    t30 = image[TABLE_30 - B:TABLE_30 - B + 16 * 32]
    tsw = image[SWITCH_TABLE - B:SWITCH_TABLE - B + 16 * 32]
    require(struct.unpack_from('<4Q', t30, 15 * 32)[0] == 0x3BB and struct.unpack_from('<4Q', tsw, 15 * 32)[0] == 0x3BB,
            'RAW extras: row tables')
    table, swaps = bytearray(tsw), 0
    for k in range(16):
        if struct.unpack_from('<Q', table, 32 * k + 8)[0] == SWITCH_ACTION:
            struct.pack_into('<Q', table, 32 * k + 8, entries['extras_toggle'])
            swaps += 1
    require(swaps == 3, 'RAW extras: switch table actions')
    yield TABLE_30, bytes(t30), bytes(table), EXTRAS + ': state 0x30 row table (switch rows, extras_toggle)'

    # C20 at runtime: label, shooting-display icon pair and C15 pre-release frames (hooks.S).
    for site, word, name, link in C20_SITES:
        old = struct.pack('<I', word)
        require(image[site - B:site - B + 4] == old, f'RAW extras: unexpected C20 site {site:#x}')
        yield site, old, branch(site, entries[name], link), EXTRAS + f': C20 switch ({name})'
