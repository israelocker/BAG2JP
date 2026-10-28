import sys,struct,capstone
p,base=sys.argv[1],int(sys.argv[2],16)
d=open(p,'rb').read()[12:]
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32); md.skipdata=True
for i in md.disasm(d,base): print("%08x  %08x  %s %s"%(i.address,struct.unpack('<I',i.bytes)[0] if len(i.bytes)==4 else 0,i.mnemonic,i.op_str))
