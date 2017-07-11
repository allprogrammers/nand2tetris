import sys

########## Modules

class Parser:
    def __init__(self,filename):
        self.code = open(filename,"r")
        self.beginpos = self.code.tell()

    def hasMoreCommands(self):
        self.current = ""
        while(self.current ==""):
            self.current = self.code.readline()
            if not self.current:
                return False
            self.current=self.current.replace(" ","").strip()
            if "/" in self.current:
                self.current = self.current[:self.current.index("/")]
        return bool(self.current)

    def advance(self):
            return self.current

    def commandType(self):
        if self.current[0]=="@":
            return "A_COMMAND"
        if self.current[0]=="(":
            return "L_COMMAND"
        return "C_COMMAND"

    def symbol(self):
        if self.commandType() == "A_COMMAND":
            return self.current[1:]
        if self.commandType() == "L_COMMAND":
            return self.current[1:-1]

    def dest(self):
        if "=" in self.current:
            return self.current[:self.current.index("=")]
        return "null"

    def comp(self):
        if "=" in self.current:
            return self.current[self.current.index("=")+1:]
        return self.current[:self.current.index(";")]

    def jump(self):
        if ";" in self.current:
            return self.current[self.current.index(";")+1:]
        return "null"

class Code:
    def dest(self,mnemonic):
        d1,d2,d3 = 0,0,0
        if "M" in mnemonic:
            d3=1
        if "A" in mnemonic:
            d1=1
        if "D" in mnemonic:
            d2=1
        return str(d1)+str(d2)+str(d3)

    def comp(self,mnemonic):
        compDict={'0':'0101010', '1':'0111111', '-1':'0111010', 'D':'0001100','A':'0110000', '!D':'0001101', '!A':'0110001', '-D':'0001111','-A':'0110011', 'D+1':'0011111','A+1':'0110111','D-1':'0001110','A-1':'0110010','D+A':'0000010','D-A':'0010011','A-D':'0000111','D&A':'0000000','D|A':'0010101','':'xxxxxxx','M':'1110000', '!M':'1110001', '-M':'1110011', 'M+1':'1110111','M-1':'1110010','D+M':'1000010','D-M':'1010011','M-D':'1000111','D&M':'1000000', 'D|M':'1010101'}
        return compDict[mnemonic]

    def jump(self,mnemonic):
        jumpdict={"JMP":"111","JGT":"001","JGE":"011","JLT":"100","JLE":"110","JNE":"101","JEQ":"010","null":"000"}
        if mnemonic in jumpdict.keys():
            return jumpdict[mnemonic]
        return "000"

class SymbolTable:
    def __init__(self):
        self.st = {"SP":0,"LCL":1,"ARG":2,"THIS":3,"THAT":4,"R0":0,"R1":1,"R2":2,"R3":3,"R4":4,"R5":5,"R6":6,"R7":7,"R8":8,"R9":9,"R10":10,"R11":11,"R12":12,"R13":13,"R14":14,"R15":15,"SCREEN":16384,"KBD":24576}
    def addEntry(self,symbol,address):
        self.st[symbol]=address
    def contains(self,symbol):
        return symbol in self.st.keys()
    def GetAddress(self,symbol):
        return self.st[symbol]

########## Helper Functions

def usage():
    print("usage:", sys.argv[0], "<source-file>.asm")
    print("\tOutput file will be <source-file>.hack")

########## Main

def main():
    if len(sys.argv) != 2:
        usage()
        sys.exit(-1)
    inFileName = sys.argv[1]
    outFileName = sys.argv[1].split(".")[0]+".hack"

    # Assemble inFileName and write binary commands to output file.
    parser = Parser(inFileName)
    coder = Code()
    symTable = SymbolTable()
    romaddress=0
    ramaddress=16
    while parser.hasMoreCommands():
        symbol=parser.symbol()
        if parser.commandType()=="L_COMMAND":
            if (not symTable.contains(symbol)):
                symtoadd=romaddress
                symTable.addEntry(symbol,symtoadd)
            romaddress-=1
        romaddress+=1
    parser.code.seek(parser.beginpos)
    writer = open(outFileName,"w")
    while parser.hasMoreCommands():
        currentcommand=parser.advance()
        ctype=parser.commandType()
        if ctype=="A_COMMAND":
            symbol=parser.symbol()
            addtoadd=0
            if symTable.contains(symbol):
                addtoadd=symTable.GetAddress(symbol)
            else:
                if ord(symbol[0])>=ord("0") and ord(symbol[0])<=ord("9"):
                    addtoadd=int(symbol)
                else:
                    addtoadd=ramaddress
                    ramaddress +=1
                symTable.addEntry(symbol,addtoadd)
            writer.write("0"+"{0:0=15b}".format(addtoadd)+"\n")
        elif ctype=="C_COMMAND":
            bitcommand="111"
            destbit = str(coder.dest(parser.dest().strip()))
            compbit = str(coder.comp(parser.comp().strip()))
            jumpbit = str(coder.jump(parser.jump().strip()))
            bitcommand += compbit + destbit + jumpbit
            writer.write(bitcommand+"\n")

if __name__ == "__main__":
    main()
