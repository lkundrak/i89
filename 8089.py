#!/usr/bin/python3
# Intel 8089 Disassembler
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
from collections import namedtuple

Op = namedtuple('Op', ['mnem', 'form', 'bits', 'mask', 'fields'])

# where two operands are listed, first is source, second is dest
# Note ASM89 uses x86 assembler convention of dest, src
inst_set = [
    # LJMP is ADDBI with rrr=100 (TP), put earlier than ADDBI in table
    ['JMP',    [[()               , '10001000 00100000 jjjjjjjj']]],

    # LJMP is ADDI with rrr=100 (TP), put earlier than ADDI in table
    ['LJMP',   [[()               , '10010001 00100000 jjjjjjjj jjjjjjjj']]],
    
    ['MOV',    [[('memo', 'reg')  , 'rrr00011 100000mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa1 100000mm'],
                [('reg',  'memo') , 'rrr00011 100001mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa1 100001mm'],
                [('memo', 'memo') , '00000011 100100mm oooooooo/00000011 110011mm oooooooo'],
                [('memo', 'mem')  , '00000011 100100mm oooooooo/00000aa1 110011mm'],
                [('mem',  'memo') , '00000aa1 100100mm/00000011 110011mm oooooooo'],
                [('mem',  'mem')  , '00000aa1 100100mm/00000aa1 110011mm']]],

    ['MOVB',   [[('memo', 'reg')  , 'rrr00010 100000mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa0 100000mm'],
                [('reg',  'memo') , 'rrr00010 100001mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa0 100001mm'],
                [('memo', 'memo') , '00000010 100100mm oooooooo/00000010 110011mm oooooooo'],
                [('memo', 'mem')  , '00000010 100100mm oooooooo/00000aa0 110011mm'],
                [('mem',  'memo') , '00000aa0 100100mm/00000010 110011mm oooooooo'],
                [('mem',  'mem')  , '00000aa0 100100mm/00000aa0 110011mm']]],

    ['MOVBI',  [[('i8',   'reg')  , 'rrr01000 00110000 iiiiiiii'],
                [('i8',   'memo') , '00001010 010011mm oooooooo iiiiiiii'],
                [('i8',   'mem')  , '00001aa0 010011mm iiiiiiii']]],

    ['MOVI',   [[('i16',  'reg')  , 'rrr10001 00110000 iiiiiiii iiiiiiii'],
                [('i16',  'memo') , '00010011 010011mm oooooooo iiiiiiii iiiiiiii'],
                [('i16',  'mem')  , '00010aa1 010011mm iiiiiiii iiiiiiii']]],

    ['MOVP',   [[('memo', 'preg') , 'ppp00011 100011mm oooooooo'],
                [('mem',  'preg') , 'ppp00aa1 100011mm'],
                [('preg', 'memo') , 'ppp00011 100110mm oooooooo'],
                [('preg', 'mem')  , 'ppp00aa1 100110mm']]],

    ['LPD' ,   [[('memo',)        , 'ppp00011 100010mm oooooooo'],
                [('mem',)         , 'ppp00aa1 100010mm']]],
    
    ['LPDI',   [[()               , 'ppp10001 00001000 iiiiiiii iiiiiiii ssssssss ssssssss']]],

    ['ADD',    [[('memo', 'reg')  , 'rrr00011 101000mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa1 101000mm'],
                [('reg',  'memo') , 'rrr00011 110100mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa1 110100mm']]],

    # ADDB encodings in 8089 assembler manual p3-12 have W bit wrong
    ['ADDB',   [[('memo', 'reg')  , 'rrr00010 101000mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa0 101000mm'],
                [('reg',  'memo') , 'rrr00010 110100mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa0 110100mm']]],

    ['ADDI',   [[('i16',  'reg')  , 'rrr10001 00100000 iiiiiiii iiiiiiii'],
                [('i16',  'memo') , '00010011 110000mm oooooooo iiiiiiii iiiiiiii'],
                [('i16',  'mem')  , '00010aa1 110000mm iiiiiiii iiiiiiii']]],

    ['ADDBI',  [[('i8',   'reg')  , 'rrr01000 00100000 iiiiiiii'],
                [('i8',   'memo') , '00001010 110000mm oooooooo iiiiiiii'],
                [('i8',   'mem')  , '00001aa0 110000mm iiiiiiii']]],

    ['INC',    [[('reg',)         , 'rrr00000 00111000'],
                [('memo',)        , '00000011 111010mm oooooooo'],
                [('mem',)         , '00000aa1 111010mm']]],

    ['INCB',   [[('memo',)        , '00000010 111010mm oooooooo'],
                [('mem',)         , '00000aa0 111010mm']]],

    ['DEC',    [[('reg',)         , 'rrr00000 00111100'],
                [('memo',)        , '00000011 111011mm oooooooo'],
                [('mem',)         , '00000aa1 111011mm']]],

    ['DECB',   [[('memo',)        , '00000010 111011mm oooooooo'],
                [('mem',)         , '00000aa0 111011mm']]],

    ['AND',    [[('memo', 'reg')  , 'rrr00011 101010mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa1 101010mm'],
                [('reg',  'memo') , 'rrr00011 110110mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa1 110110mm']]],

    ['ANDB',   [[('memo', 'reg')  , 'rrr00010 101010mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa0 101010mm'],
                [('reg',  'memo') , 'rrr00010 110110mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa0 110110mm']]],

    ['ANDI',   [[('i16',  'reg')  , 'rrr10001 00101000 iiiiiiii iiiiiiii'],
                [('i16',  'memo') , '00010011 110010mm oooooooo iiiiiiii iiiiiiii'],
                [('i16',  'mem')  , '00010aa1 110010mm iiiiiiii iiiiiiii']]],

    ['ANDBI',  [[('i8',   'reg')  , 'rrr01000 00101000 iiiiiiii'],
                [('i8',   'memo') , '00001010 110010mm oooooooo iiiiiiii'],
                [('i8',   'mem')  , '00001aa0 110010mm iiiiiiii']]],

    ['OR',     [[('memo', 'reg')  , 'rrr00011 101001mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa1 101001mm'],
                [('reg',  'memo') , 'rrr00011 110101mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa1 110101mm']]],

    ['ORB',    [[('memo', 'reg')  , 'rrr00010 101001mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa0 101001mm'],
                [('reg',  'memo') , 'rrr00010 110101mm oooooooo'],
                [('reg',  'mem')  , 'rrr00aa0 110101mm']]],

    ['ORI',    [[('i16',  'reg')  , 'rrr10001 00100100 iiiiiiii iiiiiiii'],
                [('i16',  'memo') , '00010011 110001mm oooooooo iiiiiiii iiiiiiii'],
                [('i16',  'mem')  , '00010aa1 110001mm iiiiiiii iiiiiiii']]],

    ['ORBI',   [[('i8',   'reg')  , 'rrr01000 00100100 iiiiiiii'],
                [('i8',   'memo') , '00001010 110001mm oooooooo iiiiiiii'],
                [('i8',   'mem')  , '00001aa0 110001mm iiiiiiii']]],

    ['NOT',    [[('reg',)         , 'rrr00000 00101100'],
                [('memo',)        , '00000011 110111mm oooooooo'],
                [('mem',)         , '00000aa1 110111mm'],
                [('memo', 'reg')  , 'rrr00011 101011mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa1 101011mm']]],

    ['NOTB',   [[('memo',)        , '00000010 110111mm oooooooo'],
                [('mem',)         , '00000aa0 110111mm'],
                [('memo', 'reg')  , 'rrr00010 101011mm oooooooo'],
                [('mem',  'reg')  , 'rrr00aa0 101011mm']]],

    ['SETB',   [[('memo',)        , 'bbb00010 111101mm oooooooo'],
                [('mem',)         , 'bbb00aa0 111101mm']]],

    ['CLR',    [[('memo',)        , 'bbb00010 111110mm oooooooo'],
                [('mem',)         , 'bbb00aa0 111110mm']]],

    ['CALL',   [[('memo',)        , '10001011 100111mm oooooooo jjjjjjjj'],
                [('mem',)         , '10001aa1 100111mm jjjjjjjj']]],

    ['LCALL',  [[('memo',)        , '10010011 100111mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , '10010aa1 100111mm jjjjjjjj jjjjjjjj']]],

    ['JZ',     [[('lab',  'reg')  , 'rrr01000 01000100 jjjjjjjj'],
                [('lab',  'memo') , '00001011 111001mm oooooooo jjjjjjjj'],
                [('lab',  'mem')  , '00001aa1 111001mm jjjjjjjj']]],

    ['LJZ',    [[('lab',  'reg')  , 'rrr10000 01000100 jjjjjjjj jjjjjjjj'],
                [('lab',  'memo') , '00010011 111001mm oooooooo jjjjjjjj jjjjjjjj'],
                [('lab',  'mem')  , '00010aa1 111001mm jjjjjjjj jjjjjjjj']]],

    ['JZB',    [[('memo',)        , '00001010 111001mm oooooooo jjjjjjjj'],
                [('mem',)         , '00001aa0 111001mm jjjjjjjj']]],

    ['LJZB',   [[('memo',)        , '00010010 111001mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , '00010aa0 111001mm jjjjjjjj jjjjjjjj']]],

    ['JNZ',    [[('lab',  'reg')  , 'rrr01000 01000000 jjjjjjjj'],
                [('lab',  'memo') , '00001011 111000mm oooooooo jjjjjjjj'],
                [('lab',  'mem')  , '00001aa1 111000mm jjjjjjjj']]],

    ['LJNZ',   [[('lab',  'reg')  , 'rrr10000 01000000 jjjjjjjj jjjjjjjj'],
                [('lab',  'memo') , '00010011 111000mm oooooooo jjjjjjjj jjjjjjjj'],
                [('lab',  'mem')  , '00010aa1 111000mm jjjjjjjj jjjjjjjj']]],

    ['JNZB',   [[('memo',)        , '00001010 111000mm oooooooo jjjjjjjj'],
                [('mem',)         , '00001aa0 111000mm jjjjjjjj']]],

    ['LJNZB',  [[('memo',)        , '00010010 111000mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , '00010aa0 111000mm jjjjjjjj jjjjjjjj']]],

    ['JMCE',   [[('memo',)        , '00001010 101100mm oooooooo jjjjjjjj'],
                [('mem',)         , '00001aa0 101100mm jjjjjjjj']]],

    ['LJMCE',  [[('memo',)        , '00010010 101100mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , '00010aa0 101100mm jjjjjjjj jjjjjjjj']]],

    ['JMCNE',  [[('memo',)        , '00001010 101101mm oooooooo jjjjjjjj'],
                [('mem',)         , '00001aa0 101101mm jjjjjjjj']]],

    ['LJMCNE', [[('memo',)        , '00010010 101101mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , '00010aa0 101101mm jjjjjjjj jjjjjjjj']]],

    ['JBT',    [[('memo',)        , 'bbb01010 101111mm oooooooo jjjjjjjj'],
                [('mem',)         , 'bbb01aa0 101111mm jjjjjjjj']]],

    ['LJBT',   [[('memo',)        , 'bbb10010 101111mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , 'bbb10aa0 101111mm jjjjjjjj jjjjjjjj']]],

    ['JNBT',   [[('memo',)        , 'bbb01010 101110mm oooooooo jjjjjjjj'],
                [('mem',)         , 'bbb01aa0 101110mm jjjjjjjj']]],

    ['LJNBT',  [[('memo',)        , 'bbb10010 101110mm oooooooo jjjjjjjj jjjjjjjj'],
                [('mem',)         , 'bbb10aa0 101110mm jjjjjjjj jjjjjjjj']]],

    ['TSL',    [[('memo',)        , '00011010 100101mm oooooooo iiiiiiii jjjjjjjj'],
                [('mem',)         , '00011aa0 100101mm iiiiiiii jjjjjjjj']]],

    ['WID',    [[()               , '1sd00000 00000000']]],

    ['XFER',   [[()               , '01100000 00000000']]],

    ['SINTR',  [[()               , '01000000 00000000']]],

    ['HLT',    [[()               , '00100000 01001000']]],

    ['NOP',    [[()               , '00000000 00000000']]]
]


inst_by_opcode = { }


def byte_parse(bs, second_flag):
    b = 0
    m = 0
    f = { }
    for i in range(8):
        c = bs[7-i]
        if c == '0':
            m |= (1 << i)
        elif c == '1':
            b |= (1 << i)
            m |= (1 << i)
        else:
            if second_flag:
                c += '2'
            if c not in f:
                f[c] = 0
            f[c] |= (1 << i)
    return b, m, f

def encoding_parse(encoding):
    ep_debug = False
    if ep_debug:
        print('encoding', encoding)
    encoding = encoding.replace(' ', '')
    bits = []
    mask = []
    fields = { }
    second_flag = False
    i = 0
    while len(encoding):
        if encoding[0] == '/':
            encoding = encoding[1:]
            second_flag = True
            continue
        assert len(encoding) >= 8
        byte = encoding[0:8]
        encoding = encoding[8:]
        if ep_debug:
            print('byte', byte)
        b, m, f = byte_parse(byte, second_flag)
        if ep_debug:
            print('b: ', b, 'm:', m, 'f:', f)
        bits.append(b)
        mask.append(m)
        for k in f:
            if k not in fields:
                fields[k] = [0x00] * (i)
            fields[k].append(f[k])
        i += 1
    if ep_debug:
        print('fields before:', fields)
    for k in fields:
        if len(fields[k]) < i:
            fields[k] += [0x00] * (i - len(fields[k]))
    if ep_debug:
        print('fields after:', fields)
    return bits, mask, fields


def opcode_init():
    for mnem, details in inst_set:
        for form, encoding in details:
            bits, mask, fields = encoding_parse(encoding)
            opcode = bits[1] & 0xfc
            if opcode not in inst_by_opcode:
                inst_by_opcode[opcode] = []
            inst_by_opcode[opcode].append(Op(mnem, form, bits, mask, fields))
            #print(inst, form, "%02x" % opcode)


def opcode_table_print():
    print(inst_by_opcode[0])
    for opcode in sorted(inst_by_opcode.keys()):
        for mnem, form, bits, mask, fields in inst_by_opcode[opcode]:
            print("%02x:" % opcode, mnem, bits, mask, fields)



def extract_field(inst, op, f):
    v = 0
    for i in reversed(range(min(len(inst), len(op.fields[f])))):
        for j in reversed(range(8)):
            if op.fields[f][i] & (1 << j):
                v = (v << 1) | ((inst[i] >> j) & 1)
    return v
    

def opcode_match(fw, pc, op):
    fields = { }

    l = len(op.bits)
    inst = fw[pc:pc+l]

    for i in range(l):
        if inst[i] & op.mask[i] != op.bits[i] & op.mask[i]:
            return None, fields

    for f in op.fields:
        fields[f] = extract_field(inst, op, f)

    # 'j' jump target field is relative to address of next instruction
    if 'j' in fields:
        fields['j'] += pc + l

    return len(op.bits), fields


class BadInstruction(Exception):
    pass


def opcode_search(fw, pc):
    opcode = fw[pc+1] & 0xfc
    if opcode not in inst_by_opcode:
        #print('addr %04x: opcode of inst %02x %02x not in table' % (pc, fw[pc], fw[pc+1]))
        raise BadInstruction
    for op in inst_by_opcode[opcode]:
        l, fields = opcode_match(fw, pc, op)
        if l is not None:
            return l, op, fields
    #print('addr %04x: inst %02x %02x not matched' % (pc, fw[pc], fw[pc+1]))
    raise BadInstruction

def ihex(v):
    s = '%xh' % v
    if s[0].isalpha():
        s = '0' + s
    return s

def disassemble_inst(fw, pc):
    try:
        length, op, fields = opcode_search(fw, pc)
    except BadInstruction:
        return 1, 'db %s' % ihex(fw[pc]), {}

    s = op.mnem
    for f in fields:
        s += ' %s:%x' % (f, fields[f])
    return length, s, fields

def pass1(fw):
    symtab_by_value = {}
    pc = 0
    while pc < len(fw) - 2:
        (length, dis, fields) = disassemble_inst(fw, pc)
        if 'j' in fields:
            symtab_by_value[fields['j']] = 'x%04x' % fields['j']
        pc += length
    return symtab_by_value

def pass2(fw, symtab_by_value, show_obj = False, output_file = sys.stdout):
    pc = 0
    while pc < len(fw) - 2:
        s = ''
        (length, dis, fields) = disassemble_inst(fw, pc)
        if show_obj:
            s += '%04x: '% pc
            for i in range(6):
                if (i < length):
                    s += '%02x ' % fw[pc + i]
                else:
                    s += '   '
        if pc in symtab_by_value:
            label = symtab_by_value[pc] + ':'
        else:
            label = ''
        s += '%-8s%s' % (label, dis)
        pc += length
        output_file.write(s + '\n')
    
def disassemble(fw, show_obj = False, output_file = sys.stdout):
    symtab_by_value = pass1(fw)
    #symtab_by_name = { v: k for k, v in symtab_by_value.items() }

    pass2(fw, symtab_by_value, show_obj = show_obj, output_file = output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--listing', action='store_true',
                        help = 'generate output in listing format')
    parser.add_argument('binary_file', type = argparse.FileType('rb'),
                        help = 'raw binary file containing 8089 code')
    parser.add_argument('output_file', type=argparse.FileType('w'),
                        nargs = '?',
                        default = sys.stdout,
                        help = 'disassembly output file')
    args = parser.parse_args()

    opcode_init()
    #opcode_table_print()

    fw = bytearray(args.binary_file.read())
    args.binary_file.close()

    disassemble(fw, show_obj = args.listing, output_file = args.output_file)
