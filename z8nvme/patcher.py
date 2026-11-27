"""z8nvme, HN29 "Fast card writes" (see nvme.c): one hook, the NVMe pass-through pointer.

Photo/RAW selections only: the unit (0x40A12000) and its RAM alias page lie in the video groups' area.
"""
import struct
from z8prores.package import require

BASE = 0x40160000
CODE_AT, CODE_END = 0x40A12000, 0x40A1A000


def _movz(rd, imm):
    return struct.pack('<I', 0xD2800000 | (imm << 5) | rd)


def _movk16(rd, imm):
    return struct.pack('<I', 0xF2A00000 | (imm << 5) | rd)


def edits(eg, code, symbols):
    table = int(symbols['nvme_table']['va'], 16)
    require(table == CODE_AT and CODE_AT + len(code) <= CODE_END, 'z8nvme: unit placement')
    require(code[0x14:0x18] == b'NVMD', 'z8nvme: table magic')
    require(not any(eg[CODE_AT - BASE:0x40A1B000 - BASE]), 'z8nvme: code/state area not free')
    out = []

    def put(va, new, old, why):
        off = va - BASE
        require(eg[off:off + len(old)] == old, 'z8nvme: stock bytes differ at ' + hex(va))
        out.append(dict(offset=off, old=old, new=new, purpose='z8nvme: ' + why))

    put(0x40271F48, _movz(9, table & 0xFFFF), _movz(9, 0x78B0), 'NVMe pass-through pointer (stock 0x402778b0), low half')
    put(0x40271F70, _movk16(9, table >> 16), _movk16(9, 0x4027), 'NVMe pass-through pointer, high half')
    out.append(dict(offset=CODE_AT - BASE, old=bytes(len(code)), new=code, purpose='z8nvme: code (HN29 Fast card writes)'))
    return out
