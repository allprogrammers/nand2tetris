#commandline arguments
import sys

#for directory listing
from os import listdir

#for regular expressions
import re


class JackTokenizer:
    def __init__ (self,filename):
        temp = open(filename,"r").read()
        temp = re.sub(r'//.*',"",temp)
        temp = re.sub(r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)','',temp,flags=re.DOTALL)
        self.source = temp.strip()
        self.tokenposs = {"KEYWORD":["class","constructor","function","method","field","static","var","int","char","boolean","void","true","false","null","this","let","do","if","else","while","return"],"SYMBOL":["(",")","[","]","{","}","+","-","*","/","&","|","~",",",".",";","<",">","="]}
        self.pos = -1
        self.stringseparator()
        self.tokens()

        self.emptyremover()

    def stringseparator(self):
        self.tokenizedstrlist = []
        str1 = ""
        str2 = ""
        state = False
        for i in self.source:
            if state:
                if i == "\"":
                    state = False
                    str2 +="\""
                    self.tokenizedstrlist.append(str2)
                    str2 =""
                    continue
                str2 +=i
            else:
                if i == "\"":
                    state = True
                    self.tokenizedstrlist.append(str1)
                    str1=""
                    str2 +=i
                    continue
                str1 +=i
        self.tokenizedstrlist.append(str1)

    def tokens(self):
        self.onemore = []
        self.tokens1 = []
        for i in self.tokenizedstrlist:
            if "\"" == i[0]:
                self.onemore.append(i)
                self.tokens1.append(i)
            else:
                str1 = ""
                for j in i:
                    if j in self.tokenposs["SYMBOL"]:
                        str1 += " "+j+" "
                        continue
                    str1+=j
                self.tokens1 += str1.strip("\n").strip("\t").split(" ")
                self.onemore.append(str1)

    def emptyremover(self):
        self.tokens2 = []
        for i in self.tokens1:
            if "" !=i.strip():
                self.tokens2.append(i.strip())
        #print(self.tokens2)

    def hasMoreTokens(self):
        self.pos +=1
        if self.pos <len(self.tokens2):
            self.current = self.tokens2[self.pos]
            return True
        return False

    def tokenType(self):
        if self.current in self.tokenposs["KEYWORD"]:
            return "KEYWORD"
        if self.current in self.tokenposs["SYMBOL"]:
            return "SYMBOL"
        if self.current[0] == "\"":
            return "STRING_CONST"
        if self.current[0].isdigit():
            return "INT_CONST"
        return "IDENTIFIER"

    def keyword(self):
        if self.tokenType()!="KEYWORD":
            return ""
        return self.current

    def symbol(self):
        if self.tokenType()!="SYMBOL":
            return ""
        if self.current == "<":
            return "&lt;"
        if self.current == ">":
            return "&gt;"
        if self.current =="\"":
            return "&quot;"
        if self.current == "&":
            return "&amp;"
        return self.current

    def intVal(self):
        if self.tokenType()!="INT_CONST":
            return ""
        return int(self.current)

    def identifier(self):
        if self.tokenType()!="IDENTIFIER":
            return ""
        return self.current

    def stringVal(self):
        if self.tokenType()!="STRING_CONST":
            return ""
        return self.current[1:-1]

class CompilationEngine:

    def __init__ (self,infilename,outfilename):
        self.tk = JackTokenizer(infilename)
        self.tokenstream = self.tk.tokens2
        we = open(outfilename,"w")
        self.w = we.write
        self.compileClass()
        self.pos = 0

    def compileClass(self):
        self.w("<class>\n<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        self.w("<symbol>{</symbol>\n")
        self.pos +=1
        while self.tokenstream[self.pos] in ["static","field"]
            self.compileClassVarDec()
        while self.tokenstream[self.pos] in ["constructor","function","method"]:
            self.compileSubroutine()
        self.w("<symbol>"+self.tokenstream[self.pos]+"</symbol>\n")
        self.w("</class>")

    def compileClassVarDec(self):
        self.w("<classVarDec>\n<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
        self.pos +=1
        ans = "keyword" if self.tokenstream[self.pos] in self.tk.tokenposs["KEYWORD"] else "identifier"
        self.w("<"+ans+">"+self.tokenstream[self.pos]+"</"+ans+">\n")
        #self.w("<type>"+self.tokenstream[self.pos]+"</type>\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        while self.tokenstream[self.pos] ==",":
            self.w("<symbol>,</symbol>\n")
            self.pos +=1
            self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
            self.pos +=1
        self.w("<symbol>;</symbol>\n")
        self.w("</classVarDec>\n")
        self.pos +=1

    def compileSubroutine(self):
        self.w("<subroutineDec>\n<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
        self.pos +=1
        ans = "keyword" if self.tokenstream[self.pos] in self.tk.tokenposs["KEYWORD"] else "identifier"
        self.w("<"+ans+">"+self.tokenstream[self.pos]+"</"+ans+">\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        self.w("<symbol>(</symbol>\n")
        self.pos +=1
        self.compileParameterList()
        self.w("<symbol>)</symbol>\n")
        self.pos +=1
        self.w("<subroutineBody>\n")
        self.w("<symbol>{</symbol>\n")
        self.pos +=1
        while self.tokenstream[self.pos] == "var":
            self.compileVarDec()
        self.compileStatements()
        self.w("<symbol>}</symbol>\n")
        self.w("</subroutineBody>\n")
        self.w("</subroutineDec>\n")

    def compileVarDec(self):
        self.w("<varDec>\n")
        self.w("<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
        self.pos +=1
        ans = "keyword" if self.tokenstream[self.pos] in self.tk.tokenposs["KEYWORD"] else "identifier"
        self.w("<"+ans+">"+self.tokenstream[self.pos]+"</"+ans+">\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        while self.tokenstream[self.pos]==",":
            self.w("<symbol>,</symbol>\n")
            self.pos +=1
            self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
            self.pos +=1
        self.w("<symbol>;</symbol>")
        self.pos +=1
        self.w("</varDec>\n")

    def compileStatements(self):
        self.w("<statements>\n")
        statedict = {"do":self.compileDo,"let":self.compileLet,"return":self.compileReturn,"if":self.compileIf,"while":self.compileWhile()}
        while self.tokenstream[self.pos]==['let','if','while','do','return']:
            statename = self.tokenstream[self.pos]
            self.w("<"+statename+"Statement>\n")
            statedict[statename]()
            self.w("</"+statename+"Statement>\n")
        self.w("</statements>\n")

    def compileParameterList(self):
        self.w("<parameterList>\n")
        self.w("<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        while self.tokenstream[self.pos]==",":
            self.w("<symbol>,</symbol>\n")
            self.pos+=1
            self.w("<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
            self.pos +=1
            self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
            self.pos +=1
        self.w("</parameterList>\n")

    def compileDo(self):
        self.w("<keyword>let</keyword>\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        self.w("<symbol>(</symbol>\n")
        self.pos +=1
        self.compileExpressionList()
        self.w("<symbol>)</symbol>\n")
        self.pos +=1

    def compileLet(self):
        self.w("<keyword>let</keyword>\n")
        self.pos +=1
        self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
        self.pos +=1
        self.compileExpression()
        self.w("<symbol>;</symbol>\n")
        self.pos +=1

    def compileIf(self):
        self.w("<keyword>if</keyword>\n")
        self.pos +=1
        self.w("<symbol>(</symbol>\n")
        self.pos +=1
        self.compileExpression()
        self.w("<symbol>)</symbol>\n")
        self.pos +=1
        self.w("<symbol>{</symbol>\n")
        self.pos +=1
        self.compileStatements()
        self.w("<symbol>}</symbol>\n")
        self.pos +=1
        if self.tokenstream[self.pos] == "else":
            self.w("<keyword>else</keyword>\n")
            self.pos +=1
            self.w("<symbol>{</symbol>\n")
            self.pos +=1
            self.compileStatements()
            self.w("<symbol>}</symbol>\n")
            self.pos +=1

    def compileWhile(self):
        self.w("<keyword>while</keyword>\n")
        self.pos +=1
        self.w("<symbol>(</symbol>\n")
        self.pos +=1
        self.compileExpression()
        self.w("<symbol>)</symbol>\n")
        self.pos +=1
        self.w("<symbol>{</symbol>\n")
        self.pos +=1
        self.compileStatements()
        self.w("<symbol>}</symbol>\n")
        self.pos +=1

    def compileReturn(self):
        self.w("<keyword>return</keyword>\n")
        self.pos +=1
        if self.tokenstream[self.pos] != ";":
            self.compileExpression()
        self.w("<symbol>;</symbol>\n")
        self.pos +=1

    def __compileTerm__(self):
        self.w("<term>\n")
        if self.tokenstream[self.pos]=="(":
            self.w("<symbol>(</symbol>\n")
            self.pos +=1
            self.compileExpression()
            self.w("<symbol>)</symbol>\n")
            self.pos +=1
        elif self.tokenstream[self.pos].isdigit():
            self.w("<integerConstant>"+self.tokenstream[self.pos]+"</integerConstant>")
            self.pos +=1
        elif self.tokenstream[self.pos] in ["-","~"]:
            self.w("<symbol>"+self.tokenstream[self.pos]+"</symbol>")
            self.pos +=1
            self.__compileTerm__()
        elif self.tokenstream[self.pos] in self.tk.tokenposs["KEYWORDS"]:
            self.w("<keyword>"+self.tokenstream[self.pos]+"</keyword>\n")
            self.pos+=1
        elif self.tokenstream[self.pos][0]=="\"":
            self.w("<stringConstant>"+self.tokenstream[self.pos][1:-1]+"</stringConstant>\n")
            self.pos +=1
        else:
            self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
            self.pos+=1
            if self.tokenstream[self.pos] == ".":
                self.w("<symbol>.</symbol>\n")
                self.pos +=1
                self.w("<identifier>"+self.tokenstream[self.pos]+"</identifier>\n")
                self.pos +=1
            if self.tokenstream[self.pos] == "(":
                self.w("<symbol>(</symbol>\n")
                self.pos +=1
                self.compileExpressionList()
                self.w("<symbol>)</symbol>\n")
                self.pos +=1
            elif self.tokenstream[self.pos] == "[":
                self.w("<symbol>[</symbol>\n")
                self.pos +=1
                self.compileExpression()
                self.w("<symbol>]</symbol>\n")
                self.pos +=1

        self.w("</term>\n")

    def compileExpression(self):
        self.w("<expression>\n")
        condition = True
        while condition:
            self.w("<term>")
            self.
        self.w("</expression>")

def usage():
    print("usage:",sys.argv[0],"<source-file>.jack or <source-dir>")
    print("\tOutput file will be <source-file.asm or <source-dir>/<source-dir>.xml")

def outnamegen(filename):
    i = len(filename)-1
    while filename[i]!=".":
        i -=1
    return filename[:i]

def main():
    if len(sys.argv) != 2:
        usage()
        sys.exit(-1)

    singlefilename = sys.argv[1]
    inFilenames = [sys.argv[1]+i for i in listdir(sys.argv[1]) if ".jack" in i] if not ".jack" in sys.argv[1] else [sys.argv[1]]

    for inFilename in inFilenames:
        #tk = JackTokenizer(inFilename)
        ce = CompilationEngine(inFilename,outnamegen(inFilename)+".xml")
        #outfilename=outnamegen(inFilename)+"T.xml"
        #outputfile = open(outfilename,"w")
        #outputfile.write("<tokens>\n")
        #while tk.hasMoreTokens():
            #surrtags = {"KEYWORD":["<keyword>",tk.keyword()],"IDENTIFIER":["<identifier>",tk.identifier()],"SYMBOL":["<symbol>",tk.symbol()],"INT_CONST":["<integerConstant>",str(tk.intVal())],"STRING_CONST":["<stringConstant>",tk.stringVal()]}
            #ttype = tk.tokenType()
            #text = surrtags[ttype][0]+" "+surrtags[ttype][1]+" "+"</"+surrtags[ttype][0][1:]+"\n"
            #outputfile.write(text)
        #outputfile.write("</tokens>")

if __name__ == "__main__":
    main()
