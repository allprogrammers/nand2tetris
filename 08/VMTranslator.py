import sys
from os import listdir

class Parser:
    def __init__(self,filename):
        self.code = open(filename,"r")
        self.beginpos=self.code.tell()

    def HasMoreCommands(self):
        self.current = ""
        while (self.current ==""):
            self.current = self.code.readline()
            if not self.current:
                return False
            self.current=self.current.strip()
            if "/" in self.current:
                self.current = self.current[:self.current.index("/")]
        return bool(self.current)

    def advance(self):
        return self.current

    def commandType(self):
        self.bcurrent = self.current.split()
        if self.bcurrent[0] in ["add","sub","neg","eq","gt","lt","and","or","not"]:
            return "C_ARITHMETIC"
        if self.bcurrent[0] in ["push","pop"]:
            return "C_"+self.bcurrent[0].upper()
        if self.bcurrent[0] in ["goto","label","call","return","function"]:
            return "C_"+self.bcurrent[0].upper()
        if self.bcurrent[0] == "if-goto":
            return "C_IF"

    def arg1(self):
        return self.bcurrent[0] if self.commandType() == "C_ARITHMETIC" else self.bcurrent[1]

    def arg2(self):
        return self.bcurrent[2]

class CodeWriter:
    def __init__(self,outfilename):
        self.ofile = open(outfilename,"w")
        self.push_d = "@SP\nM=M+1\nA=M-1\nM=D\n"
        self.pop_d = "@SP\nAM=M-1\nD=M\n"
        self.pop_a = "@SP\nAM=M-1\nA=M\n"
        self.counter =0
        self.fname = ""
        self.writeInit()

    def setFileName(self,filename):
        self.currentClass = filename.split(".")[0]
        self.counter=0

    def writeInit(self):
        self.ofile.write("@256\nD=A\n@SP\nM=D\n")
        self.writeCall("Sys.init",0)

    def writeLabel(self,label):
        codetowrite = "("+self.fname+"$"+label+")\n"
        self.ofile.write(codetowrite)

    def writeGoto(self,label):
        codetowrite="@"+self.fname+"$"+label+"\n0;JMP\n"
        self.ofile.write(codetowrite)

    def writeIf(self,label):
        codetowrite= self.pop_d + "@"+self.fname+"$"+label+"\nD;JNE\n"
        self.ofile.write(codetowrite)

    def writeFunction(self,functionName,numLocals):
        self.fname = functionName
        codetowrite = "("+functionName+")\n"
        codetowrite +="@"+str(numLocals)+"\nD=A\n@tempoo\nM=D\n"
        codetowrite += "("+functionName+".init)\n"
        codetowrite += "@"+functionName+".end\nD;JLE\nM=M-1\nD=0\n"+self.push_d+"@"+functionName+".init\n0;JMP\n("+functionName+".end)\n"
        self.ofile.write(codetowrite)

    def writeCall(self,functionName,numArgs):
        codetowrite = "@"+functionName+"."+str(self.counter)+".return\nD=A\n"+self.push_d
        for i in ["LCL","ARG","THIS","THAT"]:
            codetowrite += "@"+i+"\nD=M\n"+self.push_d
        codetowrite += "@SP\nD=M\n@"+str(int(numArgs)+5)+"\nD=D-A\n@ARG\nM=D\n@SP\nD=M\n@LCL\nM=D\n"
        self.ofile.write(codetowrite)
        self.ofile.write("@"+functionName+"\n0;JMP\n")
        self.ofile.write("("+functionName+"."+str(self.counter)+".return)\n")
        self.counter+=1

    def writeReturn(self):
        codetowrite = "@LCL\nD=M\n@frame\nM=D\n@5\nA=D-A\nD=M\n@returnaddress\nM=D\n"
        self.ofile.write(codetowrite)
        self.writePushPop("pop","argument",0)
        codetowrite = "@ARG\nD=M+1\n@SP\nM=D\n"
        for i in ["THAT","THIS","ARG","LCL"]:
            codetowrite += "@frame\nAM=M-1\nD=M\n@"+i+"\nM=D\n"
        codetowrite += "@returnaddress\nA=M\n0;JMP\n"
        self.ofile.write(codetowrite)

    def writeArithmetic(self,command):
        fornow = self.currentClass+"."+str(self.counter)
        codetowrite=self.pop_d
        if command in ["add","sub","eq","lt","gt","and","or"]:
            codetowrite += self.pop_a
            if command == "add":
                codetowrite += "D=D+A\n"
            elif command == "sub":
                codetowrite += "D=A-D\n"
            elif command == "and":
                codetowrite += "D=D&A\n"
            elif command == "or":
                codetowrite += "D=D|A\n"
            elif command == "eq":
                codetowrite += "D=D-A\n@"+fornow+".EQUAL\nD;JEQ\nD=0\n@"+fornow+".END\n0;JMP\n("+fornow+".EQUAL)\nD=-1\n("+fornow+".END)\n"
            elif command == "lt":
                codetowrite += "D=D-A\n@"+fornow+".LT\nD;JGT\nD=0\n@"+fornow+".END\n0;JMP\n("+fornow+".LT)\nD=-1\n("+fornow+".END)\n"
            elif command == "gt":
                codetowrite += "D=D-A\n@"+fornow+".GT\nD;JLT\nD=0\n@"+fornow+".END\n0;JMP\n("+fornow+".GT)\nD=-1\n("+fornow+".END)\n"
        else:
            if command == "neg":
                codetowrite+="D=-D\n"
            elif command == "not":
                codetowrite+="D=!D\n"
        codetowrite+=self.push_d
        self.counter +=1
        self.ofile.write(codetowrite)

    def writePushPop(self,command,segment,index):
        segdict = {"argument":"ARG","static":self.currentClass+"."+str(index),"local":"LCL","this":"THIS","that":"THAT"}
        codetowrite = ""
        if command == "push":
            seg_load_d = ""
            if segment in ["local","argument","this","that"]:
                seg_load_d = "@"+segdict[segment]+"\nD=M\n@"+str(index)+"\nA=A+D\nD=M\n"
            elif segment in ["pointer","temp"]:
                ramaddress = (3+index) if segment=="pointer" else (5+index)
                seg_load_d = "@"+str(ramaddress)+"\nD=M\n"
            elif segment == "constant":
                seg_load_d = "@"+str(index)+"\nD=A\n"
            elif segment =="static":
                seg_load_d = "@"+segdict[segment]+"\nD=M\n"
            codetowrite = seg_load_d+self.push_d
        else:
            load_to_seg = ""
            if segment in ["local","argument","this","that"]:
                codetowrite = "@"+str(index)+"\nD=A\n@"+segdict[segment]+"\nA=M\nD=D+A\n@tempou\nM=D\n"+self.pop_d+"@tempou\nA=M\nM=D\n"
            elif segment in ["pointer","temp"]:
                ramaddress = (3+index) if segment=="pointer" else (5+index)
                codetowrite = self.pop_d+"@"+str(ramaddress)+"\nM=D\n"
            elif segment =="static":
                codetowrite = "@"+segdict[segment]+"\nM=D\n"
        self.ofile.write(codetowrite)

    def test(self,label):
        #self.ofile.write(label)
        pass

def usage():
    print("usage:", sys.argv[0], "<source-file>.vm or <source-dir>")
    print("\tOutput file will be <source-file>.asm or <source-dir>/<source-dir>.asm")

def main():
    if len(sys.argv) !=2:
        usage()
        sys.exit(-1)
    outFilename = sys.argv[1]
    filenametowrite = outFilename
    while "\\" in filenametowrite :
        filenametowrite = filenametowrite[filenametowrite.index("\\")+1:]
    finalname = outFilename+"\\"+filenametowrite+".asm"
    print(finalname)
    codewrite = CodeWriter(finalname)
    inFilesnames = [i for i in listdir(sys.argv[1]) if ".vm" in i] if not ".vm" in sys.argv[1] else sys.argv[1]
    if type(inFilesnames) != list:
        inFilesnames =[inFilesnames]
    branchfunc = {"C_GOTO":codewrite.writeGoto,"C_IF":codewrite.writeIf,"C_LABEL":codewrite.writeLabel}
    callfunc = {"C_CALL":codewrite.writeCall,"C_FUNCTION":codewrite.writeFunction}
    for inFilename in inFilesnames:
        parsed = Parser(sys.argv[1]+"\\"+inFilename)
        codewrite.setFileName(inFilename)
        while parsed.HasMoreCommands():
            codewrite.test(parsed.commandType()+"\n")
            toparse = parsed.advance()
            if parsed.commandType() == "C_ARITHMETIC":
                codewrite.writeArithmetic(parsed.arg1())
            elif parsed.commandType() in ["C_PUSH","C_POP"]:
                codewrite.writePushPop(toparse[:toparse.index(" ")],parsed.arg1(),int(parsed.arg2()))
            elif parsed.commandType() in branchfunc.keys():
                branchfunc[parsed.commandType()](parsed.arg1())
            elif parsed.commandType() in callfunc.keys():
                callfunc[parsed.commandType()](parsed.arg1(),parsed.arg2())
            elif parsed.commandType() == "C_RETURN":
                codewrite.writeReturn()

if __name__ == "__main__":
    main()
