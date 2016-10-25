#!/usr/bin/python3
# Intel 8089 definitions
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

from collections import namedtuple
from enum import Enum


# operand type
# defined outside the I89 class and with very short name because
# it will be used a lot in the __inst_set class attribute of I89
OT = Enum('OT', ['reg',   # general register (all 8)
                 'preg',  # limited subset of reg
                 'jmp',   # branch target
                 'imm',   # immediate value, 8 or 16 bit
                 'i32',   # LPDI segment, offset
                 'bit',   # bit number, 0..7
                 'wids', 'widd', # 8 or 16
                 'mem',  'mem2', # mem ref w/o offset
                 'memo', 'memo2' # mem ref w/ offset
                ])


# An instruction form is a variant of an instruction that takes
# specific operand types.
Form = namedtuple('Form', ['operands', 'encoding'])

# An instruction has a single mnemonic, but possibly multiple
# forms.
class Inst:
    def __init__(self, mnem, *forms):
        self.mnem = mnem
        self.forms = forms


class I89:
    Op = namedtuple('Op', ['mnem', 'operands', 'bits', 'mask', 'fields'])

    # Follows Intel ASM89 assembler convention for operand ordering.
    # The destination operand precedes the source operand(s).
    __inst_set = [
        # JMP is ADDBI with rrr=100 (TP), put earlier than ADDBI in table
        Inst('jmp',   Form((OT.jmp,)          , '10001000 00100000 jjjjjjjj')),

        # LJMP is ADDI with rrr=100 (TP), put earlier than ADDI in table
        Inst('ljmp',  Form((OT.jmp,)          , '10010001 00100000 jjjjjjjj jjjjjjjj')),

        Inst('mov',   Form((OT.reg,  OT.memo) , 'rrr00011 100000mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa1 100000mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00011 100001mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa1 100001mm'),
                      Form((OT.memo2,OT.memo) , '00000011 100100mm oooooooo/00000011 110011mm oooooooo'),
                      Form((OT.mem2, OT.memo) , '00000011 100100mm oooooooo/00000aa1 110011mm'),
                      Form((OT.memo2,OT.mem)  , '00000aa1 100100mm/00000011 110011mm oooooooo'),
                      Form((OT.mem2, OT.mem)  , '00000aa1 100100mm/00000aa1 110011mm')),

        Inst('movb',  Form((OT.reg,  OT.memo) , 'rrr00010 100000mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa0 100000mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00010 100001mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa0 100001mm'),
                      Form((OT.memo2,OT.memo) , '00000010 100100mm oooooooo/00000010 110011mm oooooooo'),
                      Form((OT.mem2, OT.memo) , '00000010 100100mm oooooooo/00000aa0 110011mm'),
                      Form((OT.memo2,OT.mem)  , '00000aa0 100100mm/00000010 110011mm oooooooo'),
                      Form((OT.mem2, OT.mem)  , '00000aa0 100100mm/00000aa0 110011mm')),

        Inst('movbi', Form((OT.reg,  OT.imm)  , 'rrr01000 00110000 iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00001010 010011mm oooooooo iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00001aa0 010011mm iiiiiiii')),

        Inst('movi',  Form((OT.reg,  OT.imm)  , 'rrr10001 00110000 iiiiiiii iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00010011 010011mm oooooooo iiiiiiii iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00010aa1 010011mm iiiiiiii iiiiiiii')),

        Inst('movp',  Form((OT.preg, OT.memo) , 'ppp00011 100011mm oooooooo'),
                      Form((OT.preg, OT.mem)  , 'ppp00aa1 100011mm'),
                      Form((OT.memo, OT.preg) , 'ppp00011 100110mm oooooooo'),
                      Form((OT.mem,  OT.preg) , 'ppp00aa1 100110mm')),

        Inst('lpd' ,  Form((OT.preg, OT.memo,), 'ppp00011 100010mm oooooooo'),
                      Form((OT.preg, OT.mem,) , 'ppp00aa1 100010mm')),
    
        Inst('lpdi',  Form((OT.preg, OT.i32)  , 'ppp10001 00001000 iiiiiiii iiiiiiii ssssssss ssssssss')),

        Inst('add',   Form((OT.reg,  OT.memo) , 'rrr00011 101000mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa1 101000mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00011 110100mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa1 110100mm')),

        # ADDB encodings in 8089 assembler manual p3-12 have W bit wrong
        Inst('addb',  Form((OT.reg,  OT.memo) , 'rrr00010 101000mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa0 101000mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00010 110100mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa0 110100mm')),

        Inst('addi',  Form((OT.reg,  OT.imm)  , 'rrr10001 00100000 iiiiiiii iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00010011 110000mm oooooooo iiiiiiii iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00010aa1 110000mm iiiiiiii iiiiiiii')),

        Inst('addbi', Form((OT.reg,  OT.imm)  , 'rrr01000 00100000 iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00001010 110000mm oooooooo iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00001aa0 110000mm iiiiiiii')),

        Inst('inc',   Form((OT.reg,)          , 'rrr00000 00111000'),
                      Form((OT.memo,)         , '00000011 111010mm oooooooo'),
                      Form((OT.mem,)          , '00000aa1 111010mm')),

        Inst('incb',  Form((OT.memo,)         , '00000010 111010mm oooooooo'),
                      Form((OT.mem,)          , '00000aa0 111010mm')),

        Inst('dec',   Form((OT.reg,)          , 'rrr00000 00111100'),
                      Form((OT.memo,)         , '00000011 111011mm oooooooo'),
                      Form((OT.mem,)          , '00000aa1 111011mm')),

        Inst('decb',  Form((OT.memo,)         , '00000010 111011mm oooooooo'),
                      Form((OT.mem,)          , '00000aa0 111011mm')),

        Inst('and',   Form((OT.reg,  OT.memo) , 'rrr00011 101010mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa1 101010mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00011 110110mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa1 110110mm')),

        Inst('andb',  Form((OT.reg,  OT.memo) , 'rrr00010 101010mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa0 101010mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00010 110110mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa0 110110mm')),

        Inst('andi',  Form((OT.reg,  OT.imm)  , 'rrr10001 00101000 iiiiiiii iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00010011 110010mm oooooooo iiiiiiii iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00010aa1 110010mm iiiiiiii iiiiiiii')),

        Inst('andbi', Form((OT.reg,  OT.imm)  , 'rrr01000 00101000 iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00001010 110010mm oooooooo iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00001aa0 110010mm iiiiiiii')),

        Inst('or',    Form((OT.reg,  OT.memo) , 'rrr00011 101001mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa1 101001mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00011 110101mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa1 110101mm')),

        Inst('orb',   Form((OT.reg,  OT.memo) , 'rrr00010 101001mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa0 101001mm'),
                      Form((OT.memo, OT.reg)  , 'rrr00010 110101mm oooooooo'),
                      Form((OT.mem,  OT.reg)  , 'rrr00aa0 110101mm')),

        Inst('ori',   Form((OT.reg,  OT.imm)  , 'rrr10001 00100100 iiiiiiii iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00010011 110001mm oooooooo iiiiiiii iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00010aa1 110001mm iiiiiiii iiiiiiii')),

        Inst('orbi',  Form((OT.reg,  OT.imm)  , 'rrr01000 00100100 iiiiiiii'),
                      Form((OT.memo, OT.imm)  , '00001010 110001mm oooooooo iiiiiiii'),
                      Form((OT.mem,  OT.imm)  , '00001aa0 110001mm iiiiiiii')),

        Inst('not',   Form((OT.reg,)          , 'rrr00000 00101100'),
                      Form((OT.memo,)         , '00000011 110111mm oooooooo'),
                      Form((OT.mem,)          , '00000aa1 110111mm'),
                      Form((OT.reg,  OT.memo) , 'rrr00011 101011mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa1 101011mm')),

        Inst('notb',  Form((OT.memo,)         , '00000010 110111mm oooooooo'),
                      Form((OT.mem,)          , '00000aa0 110111mm'),
                      Form((OT.reg,  OT.memo) , 'rrr00010 101011mm oooooooo'),
                      Form((OT.reg,  OT.mem)  , 'rrr00aa0 101011mm')),

        Inst('setb',  Form((OT.memo, OT.bit)  , 'bbb00010 111101mm oooooooo'),
                      Form((OT.mem,  OT.bit)  , 'bbb00aa0 111101mm')),

        Inst('clr',   Form((OT.memo, OT.bit)  , 'bbb00010 111110mm oooooooo'),
                      Form((OT.mem,  OT.bit)  , 'bbb00aa0 111110mm')),

        Inst('call',  Form((OT.memo, OT.jmp)  , '10001011 100111mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '10001aa1 100111mm jjjjjjjj')),

        Inst('lcall', Form((OT.memo, OT.jmp)  , '10010011 100111mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '10010aa1 100111mm jjjjjjjj jjjjjjjj')),

        Inst('jz',    Form((OT.reg,  OT.jmp)  , 'rrr01000 01000100 jjjjjjjj'),
                      Form((OT.memo, OT.jmp)  , '00001011 111001mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa1 111001mm jjjjjjjj')),

        Inst('ljz',   Form((OT.reg,  OT.jmp)  , 'rrr10000 01000100 jjjjjjjj jjjjjjjj'),
                      Form((OT.memo, OT.jmp)  , '00010011 111001mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa1 111001mm jjjjjjjj jjjjjjjj')),

        Inst('jzb',   Form((OT.memo, OT.jmp)  , '00001010 111001mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa0 111001mm jjjjjjjj')),

        Inst('ljzb',  Form((OT.memo, OT.jmp)  , '00010010 111001mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa0 111001mm jjjjjjjj jjjjjjjj')),

        Inst('jnz',   Form((OT.reg,  OT.jmp)  , 'rrr01000 01000000 jjjjjjjj'),
                      Form((OT.memo, OT.jmp)  , '00001011 111000mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa1 111000mm jjjjjjjj')),

        Inst('ljnz',  Form((OT.reg,  OT.jmp)  , 'rrr10000 01000000 jjjjjjjj jjjjjjjj'),
                      Form((OT.memo, OT.jmp)  , '00010011 111000mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa1 111000mm jjjjjjjj jjjjjjjj')),

        Inst('jnzb',  Form((OT.memo, OT.jmp)  , '00001010 111000mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa0 111000mm jjjjjjjj')),

        Inst('ljnzb', Form((OT.memo, OT.jmp)  , '00010010 111000mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa0 111000mm jjjjjjjj jjjjjjjj')),

        Inst('jmce',  Form((OT.memo, OT.jmp)  , '00001010 101100mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa0 101100mm jjjjjjjj')),

        Inst('ljmce', Form((OT.memo, OT.jmp)  , '00010010 101100mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa0 101100mm jjjjjjjj jjjjjjjj')),

        Inst('jmcne', Form((OT.memo, OT.jmp)  , '00001010 101101mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00001aa0 101101mm jjjjjjjj')),

        Inst('ljmcne',Form((OT.memo, OT.jmp)  , '00010010 101101mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.jmp)  , '00010aa0 101101mm jjjjjjjj jjjjjjjj')),

        Inst('jbt',   Form((OT.memo, OT.bit, OT.jmp), 'bbb01010 101111mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.bit, OT.jmp), 'bbb01aa0 101111mm jjjjjjjj')),

        Inst('ljbt',  Form((OT.memo, OT.bit, OT.jmp), 'bbb10010 101111mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.bit, OT.jmp), 'bbb10aa0 101111mm jjjjjjjj jjjjjjjj')),

        Inst('jnbt',  Form((OT.memo, OT.bit, OT.jmp), 'bbb01010 101110mm oooooooo jjjjjjjj'),
                      Form((OT.mem,  OT.bit, OT.jmp), 'bbb01aa0 101110mm jjjjjjjj')),

        Inst('ljnbt', Form((OT.memo, OT.bit, OT.jmp), 'bbb10010 101110mm oooooooo jjjjjjjj jjjjjjjj'),
                      Form((OT.mem,  OT.bit, OT.jmp), 'bbb10aa0 101110mm jjjjjjjj jjjjjjjj')),

        Inst('tsl',   Form((OT.memo, OT.imm, OT.jmp), '00011010 100101mm oooooooo iiiiiiii jjjjjjjj'),
                      Form((OT.mem,  OT.imm, OT.jmp), '00011aa0 100101mm iiiiiiii jjjjjjjj')),

        Inst('wid',   Form((OT.wids, OT.widd) , '1sd00000 00000000')),

        Inst('xfer',  Form(()                 , '01100000 00000000')),

        Inst('sintr', Form(()                 , '01000000 00000000')),

        Inst('hlt',   Form(()                 , '00100000 01001000')),

        Inst('nop',   Form(()                 , '00000000 00000000'))
    ]

    # GA, GB, GC, TP are 20-bit pointer registers w/ tag bit,
    #                    legal for r or p field
    #        tag = 0 for 20-bit system address, 1 for 16-bit local address
    #        LPD, LPDI set tag to zero (system)
    #        MOV, MOVB, MOVI, MOVBI sign extend to 20 bits and set tag to
    #                    one (local)
    #        MOVP stores, loads full pointer including tag bit
    # BC, IX, CC, MC are 16-bit registers, only legal for rrr field,
    # but not for the ppp field

    # Reg used for rrr or ppp field
    class Reg(Enum):
        ga = 0
        gb = 1
        gc = 2
        bc = 3
        tp = 4
        ix = 5
        cc = 6
        mc = 7
        
    # AReg used for aa field, as part of memory addressing
    class AReg(Enum):
        ga = 0
        gb = 1
        gc = 2
        pp = 3


    class MemoryReferenceOperand:
        def __init__(self, base_reg, indexed = False, auto_increment = False, offset = None):
            super().__init__()
            self.base_reg = base_reg
            self.offset = offset
            if indexed == False:
                assert auto_increment is False
                if offset is None:
                    self.mode = 0
                else:
                    self.mode = 1
            else:
                assert offset is None
                if auto_increment is False:
                    self.mode = 2
                else:
                    self.mode = 3


    @staticmethod
    def __byte_parse(bs, second_flag):
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

    @staticmethod
    def __encoding_parse(encoding):
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
            b, m, f = I89.__byte_parse(byte, second_flag)
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


    def __opcode_init(self):
        for inst in self.__inst_set:
            if inst.mnem not in self.__inst_by_mnemonic:
                self.__inst_by_mnemonic[inst.mnem] = inst
            for form in inst.forms:
                bits, mask, fields = self.__encoding_parse(form.encoding)
                opcode = bits[1] & 0xfc
                if opcode not in self.__inst_by_opcode:
                    self.__inst_by_opcode[opcode] = []
                self.__inst_by_opcode[opcode].append(self.Op(inst.mnem, form.operands, bits, mask, fields))
                #print(inst, operands, "%02x" % opcode)


    def _opcode_table_print(self):
        for opcode in sorted(self.__inst_by_opcode.keys()):
            for mnem, operands, bits, mask, fields in self.__inst_by_opcode[opcode]:
                print("%02x:" % opcode, mnem, operands, bits, mask, fields)



    @staticmethod
    def __extract_field(inst, op, f):
        width = 0
        v = 0
        for i in reversed(range(min(len(inst), len(op.fields[f])))):
            for j in reversed(range(8)):
                if op.fields[f][i] & (1 << j):
                    v = (v << 1) | ((inst[i] >> j) & 1)
                    width += 1
        if width == 8 and v > 127 and (f == 'i' or f == 'j'):
            v += (65536 - 256)
        return v


    def __opcode_match(self, fw, pc, op):
        fields = { }

        l = len(op.bits)
        inst = fw[pc:pc+l]

        for i in range(l):
            if inst[i] & op.mask[i] != op.bits[i] & op.mask[i]:
                return None, fields

        for f in op.fields:
            fields[f] = self.__extract_field(inst, op, f)

        # 'j' jump target field is relative to address of next instruction
        if 'j' in op.fields:
            fields['j'] = (fields['j'] + pc + l) & 0xffff

        return len(op.bits), fields


    class BadInstruction(Exception):
        pass


    def mnemonic_search(self, mnemonic):
        if mnemonic not in self.__inst_by_mnemonic:
            return None
        return self.__inst_by_mnemonic[mnemonic]


    def opcode_search(self, fw, pc):
        opcode = fw[pc+1] & 0xfc
        if opcode not in self.__inst_by_opcode:
            #print('addr %04x: opcode of inst %02x %02x not in table' % (pc, fw[pc], fw[pc+1]))
            raise I89.BadInstruction
        for op in self.__inst_by_opcode[opcode]:
            l, fields = self.__opcode_match(fw, pc, op)
            if l is not None:
                return l, op, fields
        #print('addr %04x: inst %02x %02x not matched' % (pc, fw[pc], fw[pc+1]))
        raise I89.BadInstruction

    @staticmethod
    def ihex(v):
        s = '%xh' % v
        if s[0].isalpha():
            s = '0' + s
        return s

    def __dis_mem_operand(self, fields, pos = 1):
        suffix = ['', '', '2']
        mode   = fields['a' + suffix[pos]]
        mreg   = fields['m' + suffix[pos]]
        del fields['a' + suffix[pos]], fields ['m' + suffix[pos]]
        s = '[' + self.AReg(mreg).name
        if mode == 0:
            return  s + ']'
        elif mode == 1:
            offset = fields['o' + suffix[pos]]
            del fields['o' + suffix[pos]]
            return s + '].' + self.ihex(offset)
        elif mode == 2:
            return s + '+ix]'
        else:  # mode == 3
            return s + '+ix+]'
            

    def disassemble_inst(self, fw, pc, symtab_by_value = {}, disassemble_operands = True):
        try:
            length, op, fields = self.opcode_search(fw, pc)
        except I89.BadInstruction:
            return 1, 'db      ', '%s' % self.ihex(fw[pc]), {}

        s = '%-6s' % op.mnem
        operands = []

        if disassemble_operands:
            ftemp = fields.copy()
            for operand in op.operands:
                if operand == OT.jmp:
                    target = ftemp['j']
                    del ftemp['j']
                    if target in symtab_by_value:
                        value = symtab_by_value[target]
                    else:
                        value = self.ihex(target)
                elif operand == OT.reg:
                    value = self.Reg(ftemp['r']).name
                    del ftemp['r']
                elif operand == OT.preg:
                    p = ftemp['p']
                    del ftemp['p']
                    value = self.Reg(p).name
                    if value not in ['ga', 'gb', 'gc', 'tp']:
                        value += '_bad'
                elif operand == OT.bit:
                    value = '%d' % ftemp['b']
                    del ftemp['b']
                elif operand == OT.memo:
                    ftemp ['a'] = 1
                    value = self.__dis_mem_operand(ftemp)
                elif operand == OT.mem:
                    value = self.__dis_mem_operand(ftemp)
                elif operand == OT.memo2:
                    ftemp ['a2'] = 1
                    value = self.__dis_mem_operand(ftemp, 2)
                elif operand == OT.mem2:
                    value = self.__dis_mem_operand(ftemp, 2)
                elif operand == OT.imm:
                    value = self.ihex(ftemp['i'])
                    del ftemp['i']
                elif operand == OT.i32:
                    value = self.ihex(ftemp['s']) + ':' + self.ihex(ftemp['i'])
                    del ftemp['s'], ftemp['i']
                elif operand == OT.wids:
                    value = str([8, 16][ftemp['s']])
                    del ftemp['s']
                elif operand == OT.widd:
                    value = str([8, 16][ftemp['d']])
                    del ftemp['d']
                else:
                    raise NotImplementedError('operand type ' + operand)
                operands.append(value)
            if ftemp:
                raise NotImplementedError('leftover fields: ' + str(ftemp))

        return length, s, ','.join(operands), fields


    # inst can be:
    #   Inst (return value from mnemonic_search)
    #   mnemonic (string)
    # each operand can be:
    #   register name (string or enum value)   reg, preg
    #   integer                                jmp, imm, i32, bit, wids, widd
    #   MemoryReferenceOperand                 mem, memo, mem2, memo2
    def assemble_instruction(self, pc, inst, operands):
        if not isinstance(inst, Inst):
            inst = self.mnemonic_search(inst)
            if inst is None:
                raise Exception('unrecognized mnemonic')
        return bytearray([0x12, 0x34, 0x56])


    def __init__(self):
        self.__inst_by_opcode = { }
        self.__inst_by_mnemonic = { }
        self.__opcode_init()

if __name__ == '__main__':
    i89 = I89()
    i89._opcode_table_print()
