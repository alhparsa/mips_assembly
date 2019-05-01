import argparse
addr = {}

def get_lables(f):
    print("Gathering the label addresses")
    pc_counter = 0
    for l in f.readlines():
        if ":" in l:
            addr[l[:l.find(':')]] = pc_counter
        pc_counter+=4

set_len_w_z = lambda s, size: '0b'+(size + 2 - len(bin(s))) * '0' +bin(s).split('b')[1] if s >= 0 else '0b'+(size + 3 - len(bin(s))) * bin(s)[3] +bin(s).split('b')[1]
set_len_wo_z = lambda s, size: set_len_w_z(s,size).split('b')[1]

instructions = {
    'add': (0x00,0x20),
    'addi': (0x08,0),
    'and': (0x00,0x24),
    'andi': (0x0C,0),
    'or': (0x00,0x25),
    'ori': (0x0D,0),
    'sub': (0x00,0x22),
    'sll': (0x00,0x00),
    'srl': (0x00,0x02),
    'lw': (0x23,0),
    'sw': (0x2B,0),
    'lui': (0x0F,0),
    'slt': (0x00,0x2A),
    'slti': (0x0A,0),
    'beq': (0x04,0),
    'bne': (0x05,0),
    'jal': (0x03,0),
    'jr': (0x00,0x08),
    'j': (0x02,0)
    }

regs = {'v0':'2',
        'v1':'3',
        'a0':'4',
        'a1':'5',
        'a2':'6',
        'a3':'7',
        't0':'8',
        't1':'9',
        't2':'10',
        't3':'11',
        't4':'12',
        't5':'13',
        't6':'14',
        't7':'15',
        's0':'16',
        's1':'17',
        's2':'18',
        's3':'19',
        's4':'20',
        's5':'21',
        's6':'22',
        's7':'23',
        't8':'24',
        't9':'25',
        'sp':'29',
        'ra':'31'
        }

remove_dollar_sign = lambda x: x if not '$' in x else x[x.find('$')+1:]

def r_assembler(opcode, rd, rs, rt):
    op = set_len_w_z(instructions[opcode][0], 6)
    rs = set_len_wo_z(int(regs[rs]), 5)
    rt = set_len_wo_z(int(regs[rt]), 5)
    rd = set_len_wo_z(int(regs[rd]), 5)
    filler = set_len_wo_z(0,5)
    func = set_len_wo_z(instructions[opcode][1], 6)
    machine_code = op+rs+rt+rd+filler+func
    return hex(int(machine_code, 2))

def jr_assembler(s):
    op = set_len_w_z(0,6)
    func = set_len_wo_z(0x08, 4)
    rd = set_len_wo_z(int(regs[s]),5)
    filler = set_len_wo_z(0,17)
    machine_code = op+rd+filler+func
    return(hex(int(machine_code,2)))


def shift_assembler(opcode, rd, rt, shift):
    op = set_len_w_z(instructions[opcode][0], 6)
    rt = set_len_wo_z(int(regs[rt]), 5)
    rd = set_len_wo_z(int(regs[rd]), 5)
    shift = set_len_wo_z(shift, 5)
    filler = set_len_wo_z(0,5)
    func = set_len_wo_z(instructions[opcode][1], 6)
    machine_code = op+filler+rt+rd+shift+func
    return hex(int(machine_code,2))

def r_type(s):
    s = s.replace(' ','')
    op = s.split('$')[0]
    s = s[s.find('$'):]
    if op == 'jr':
        return jr_assembler(s[1:])
    elif op in ('srl', 'sll'):
        rd, rt, shift = s.split(',')
        rd = remove_dollar_sign(rd)
        rt = remove_dollar_sign(rt)
        shift = int(shift)
        return shift_assembler(op, rd, rt, shift)
    rd, rs, rt = s.split(',')
    rd = remove_dollar_sign(rd)
    rt = remove_dollar_sign(rt)
    rs = remove_dollar_sign(rs)
    return r_assembler(op, rd, rs, rt)

def i_assembler(opcode, rs, rt, imm):
    op = set_len_w_z(instructions[opcode][0],6)
    rt = set_len_wo_z(int(regs[rt]), 5)
    rs = set_len_wo_z(int(regs[rs]), 5)
    if imm<0:
        imm = twos_complement(imm)
    imm = set_len_wo_z(imm, 16)
    machine_code = op+rs+rt+imm
    print(op, rs, rt,len(imm))
    return hex(int(machine_code,2))


def lui_assembler(op,rt,imm):
    op = set_len_w_z(instructions[op][0],6)
    rt = set_len_wo_z(int(regs[rt]), 5)
    imm = set_len_wo_z(imm, 16)
    rs = set_len_wo_z(0, 5)
    machine_code = op+rs+rt+imm
    return hex(int(machine_code,2))

def i_type(s):
    s = s.replace(' ','')
    op = s.split('$')[0]
    s = s[s.find('$'):].strip()
    if op in ('sw', 'lw'):
        rt = s[:s.find(',')]
        rt = remove_dollar_sign(rt)
        imm = s[s.find(',')+1:s.find('(')]
        imm = int(imm)
        rs = s[s.find('(')+1:s.find(')')]
        rs = remove_dollar_sign(rs)
        return i_assembler(op, rs, rt, imm)
    elif op == 'lui':
        rt = s.split(',')[0]
        rt = remove_dollar_sign(rt)
        imm = s.split(',')[1]
        imm = int(imm,16)
        return lui_assembler(op,rt,imm)
    elif op in ('beq', 'bne'): ## requires a relative address of PC = PC + 4 + offset × 4
        rt = s[s.find(',')+1:s.find(s.split(',')[-1])-2]
        rt = remove_dollar_sign(rt)
        rs = s.split(',')[0]
        rs = remove_dollar_sign(rs)
        if (addr[s.split(',')[-1]] - (pc + 4)) / 4 < 0:
            imm = twos_complement((addr[s.split(',')[-1]] - (pc + 4)) / 4)
        else:
            imm = (addr[s.split(',')[-1]] - (pc + 4)) / 4
        return i_assembler(op, rs, rt, imm)
    rt = s.split(',')[0]
    rt = remove_dollar_sign(rt)
    rs = s[s.find(',')+1:s.find(s.split(',')[-1])-2]
    rs = remove_dollar_sign(rs)
    imm = s.split(',')[-1]
    return i_assembler(op, rs, rt, imm)


def j_assembler(opcode, address):
    ''' Setting the address for jump-type instructions
    1. Get address at label in hex
    2. Drop the first hex digit
    3. Convert to binary
    4. Drop the last two bits
    '''
    op = set_len_w_z(instructions[opcode][0], 6)
    address = set_len_wo_z(bin(addr[address][1:])[:-2],26)
    machine_code = op+address
    return hex(int(machine_code,2))



def j_type(s):
    op = s.split()[0]
    s = s.replace(' ', '')
    address = s[len(op)-1:]
    return j_assembler(op, address)


def twos_complement(bin_num):
    bin_num_str = str(bin(bin_num))
    bin_num = bin_num_str[bin_num_str.find('b')+1:]
    f = lambda x: "0" if x == '1' else ('1' if x=='0' else x)
    return int("-0b"+set_len_wo_z(-1*(int(''.join([f(x) for x in bin_num]),2)+1),len(bin_num_str)-1),2)



def process_assembler(instr, outputfile):
    writeline = ""
    if instr.split()[0] in ("add", "sub", "and", "or", "sll", "srl", "jal"):
        writeline = r_type(instr)
    elif instr.split()[0] in ("j", "jr" ):
        writeline = j_type(instr)
    else:
        writeline = i_type(instr)
    if len(writeline < 10):
        filler = 10 - len(writeline)
        writeline = writeline.split('x')[0]+'b'+filler*'0'+writeline.split('x')[1]
    outputfile.writeline(writeline)

pc_counter = 0
def assembler(inputfile, outputfile):
    w = open(outputfile, 'a')
    with open(inputfile, 'r') as f:
        for l in f.readlines():
            if ':' in l:
                branch, instr = l[:l.find('\\')].split(':')
            else:
                instr = l
            res = process_assembler(instr, w)
            w.writeline(res)
            pc_counter+=4
        f.close()
    w.close()



num_to_regs = {
        2:'v0',
        3:'v1',
        4:'a0',
        5:'a1',
        6:'a2',
        7:'a3',
        8:'t0',
        9:'t1',
        10:'t2',
        11:'t3',
        12:'t4',
        13:'t5',
        14:'t6',
        15:'t7',
        16:'s0',
        17:'s1',
        18:'s2',
        19:'s3',
        20:'s4',
        21:'s5',
        22:'s6',
        23:'s7',
        24:'t8',
        25:'t9',
        29:'sp',
        31:'ra'
}


func_to_instr = {
    0x2b: "sltu",
    0x2a: "slt",
    0x27: "nor",
    0x26: "xor",
    0x25: "or",
    0x24: "and",
    0x23: "subu",
    0x22: "sub",
    0x21: "addu",
    0x20: "add",
    0x1b: "divu",
    0x1a: "div",
    0x19: "multu",
    0x18: "mult",
    0x13: "mtlo",
    0x12: "mflo",
    0x11: "mthi",
    0x10: "mfhi",
    0x08: "jr",
    0x03: "sra",
    0x02: "srl",
    0x00: "sll"

}


def get_func(instr):
    return func_to_instr[int(instr,2)]

def r_disassembler(instr):
    func_code = get_func('0b'+instr[-7:])
    if func_code in ('sll', 'srl'):
        rt = num_to_regs[int('0b'+instr[13:18],2)]
        rd = num_to_regs[int('0b'+instr[18:23],2)]
        shift = int('0b'+instr[23:28],2)
        return f'{func_code} ${rd}, ${rt}, {shift}'
    rs = num_to_regs[int('0b'+instr[8:13],2)]
    rt = num_to_regs[int('0b'+instr[13:18],2)]
    rd = num_to_regs[int('0b'+instr[18:23],2)]
    return f'{func_code} ${rd}, ${rs}, ${rt}'


def j_disassembler(instr):
    op_code = instr[:8]
    if int(op_code,2) == 2: ## if it's j
        op_code = 'j '
    elif int(op_code,2) == 3: ## if it's jal
        op_code = 'jal '
    address = int('0b' + instr[8:],2)
    return  op_code + str(address)




op_codes = {0x08:"addi",
            0x09:"addiu",
            0x0c:"andi",
            0x04:"beq",
            0x06:"blez",
            0x05:"bne",
            0x07:"bgtz",
            0x20:"lb",
            0x24:"lbu",
            0x25:"lhu",
            0x0f:"lui",
            0x23:"lw",
            0x0d:"ori",
            0x28:"sb",
            0x29:"sh",
            0x0a:"slti",
            0x0b:"sltiu",
            0x2b:'sw'}


set_len_w_z_twos_complement = lambda s, size: '0b'+(size + 2 - len(bin(s))) * '0' +bin(s).split('b')[1]
def twos_complemnt_neg(num):
    num_str = str(bin(num))
    num = num_str[num_str.find('b')+1:]
    f = lambda x: "0" if x == '1' else ('1' if x=='0' else x)
    return -1*int(set_len_w_z_twos_complement(-1*(int(''.join([f(x) for x in num]),2)+1),len(num)-1),2)



def get_op_code(op_code):
    op_code = int(op_code,2)
    return op_codes[op_code]


def i_disassembler(instr):
    op_code = instr[:8]
    op_code = get_op_code(op_code)
    imm = int('0b'+instr[-16:],2)
    if imm>=40960:
        imm = twos_complemnt_neg(imm)
    rs = num_to_regs[int('0b'+instr[8:13],2)]
    rt = num_to_regs[int('0b'+instr[13:18],2)]
    if op_code in ('lw', 'sw'):
        return f"{op_code} ${rt}, {imm}(${rs})"
    else:
        return f"{op_code} ${rt}, ${rs}, {imm}"






def process_disassembler(instr):
    instr = bin(instr)
    if not len(instr)==34:
        instr = set_len_w_z(int(instr,2),32)
    if (int(instr[:8],2) == 0):
        return r_disassembler(instr)
    elif int(instr[:8],2) in (2,3):
        return j_disassembler(instr)
    else:
        return i_disassembler(instr)




def disassembler(inputfile, outputfile):
    output = open(outputfile, 'a')
    with open(inputfile, 'r') as f:
        for l in f.readlines():
            inst = l
            if '\n' in l:
                inst = l[:'\\']
            res = process_disassembler(inst)
            outputfile.writeline(res)
        f.close()
    output.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Assembler and disassembler script')
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('-m', '--mode', help='Set it to be assembler or disassembler, can only be set to \"a\" or \"d\"', default = 'a',required = True)
    requiredNamed.add_argument('-i', '--input', help='Input file location',required=True)
    requiredNamed.add_argument('-o', '--output', help='Output file location', default = 'out.txt',required=True)
    args = parser.parse_args()
    inputfile = args.input
    outputfile = args.output
    mode = args.mode
    if not mode in ('d', 'a'):
        raise ValueError("Mode can be only set to \"a\" or \"d\"")
    else:
        if mode == 'a':
            get_lables(open(inputfile, 'r'))
            assembler(inputfile, outputfile)
        else:
            disassembler(inputfile, outputfile)
