import os
import sys
import fnmatch 
import subprocess
import re

class Graph:
    def __init__(self, path = sys.argv[1], showFunctions = True):
        # initializing dictionaries to produce links
        self.__functionNames = {}
        self.__importNames = {}
        self.__pathNames = {}
        
        # init path
        self.path = path

        # load files in path
        self.files = self.__loadFiles()
        # init showFunctions
        self.__showFunctions = showFunctions

        # init Graph header
        self.Graph = "digraph G {\n"

        # init display styles of structures
        self.functionStyle = "node [style = \"rounded,dotted\",color=\"black\", shape= \"box\", fontname = \"Arial\", fontsize = \"16\"]\n"
        self.emptyFileStyle = "node [style = \"solid,rounded\",color = \"red\", shape = \"box\", fontname = \"Arial\", fontsize = \"14\"]\n"
        self.fileStyle = "style=\"rounded\"\ncolor=\"red\"\nfontname=\"Arial\"\nfontsize=\"20\"\n"
        self.classStyle = "style=\"solid\"\ncolor=\"blue\"\nfontname=\"Arial\"\nfontsize=\"20\"\n"
        self.folderStyle = "style=\"solid\"\ncolor=\"black\"\nfontname=\"Arial\"\nfontsize=\"20\"\n"

        # init display styles of links
        self.arrowStyleImportFunction = [" -> ", "[style=dashed, color=grey]"]
        self.arrowStyleFromFile = [" -> ", "[color=green]"]
        self.arrowStyleImportFile = [" -> ", "[penwidth=2, arrowhead=none, color=magenta]"]
        self.Graph += "splines=\"compound\";\n"

        # generate structure for Graph
        self.Graph += self.genCodeGraph(self.files)
        
        # generate links for Graph
        self.Graph += self.genConnections(self.files)

        # finalize Graph
        self.Graph += "}\n"

    
    def __loadFiles(self):
        files = []
        
        for root, dirnames, filenames in os.walk(self.path):
            for f in fnmatch.filter(filenames, '*.py'):
                file = os.path.join(root, f)
                file = re.sub(self.path, "", file)
                files += [file]
        files = [f.split("/")[1:] for f in files]
        return files 

    def __filterList(self, list):
        newList = []
        for elem in list:
            if re.match(r'\ *def\ .*\(.*\):', elem):
                newList += [elem]
            if re.match(r'^class\ .*:', elem):
                newList += [elem]
        return newList

    def __getIndentation(self, list):
        foundIndentation = None
        while len(list) > 0 and not foundIndentation:
            if list[0].startswith("    def "):
                foundIndentation = "    "
            elif list[0].startswith("  def "):
                foundIndentation = "  "
            else:
                list.pop(0)
        return foundIndentation, list

    def __genCodeFunction(self, pyCodeLine, filename, prefix):
        functionName = re.findall(r'def\ .*?\(', pyCodeLine)
        try:
            functionName = functionName[0][4:-1]
        except:
            return ""
        nodeNameFunction = "_".join(prefix)+"_"+filename+"_"+functionName
        pathToFunction = "/".join(prefix)+"/"+filename+".py"
        self.__functionNames[filename+":"+functionName] = nodeNameFunction
        graphCode = self.functionStyle
        graphCode += nodeNameFunction.replace("-","")+" [label=\""+functionName.replace("-","")+"\"];\n"
        return graphCode

    def __genCodeFile(self,file,prefix):
        filename = file[-1][:-3]
        path = self.path + "/"+"/".join(prefix)+"/"+file[-1]
        definedFunctions = subprocess.Popen("grep 'def ' "+path, shell = True, stdout = subprocess.PIPE).stdout.read()
        definedFunctions = definedFunctions.split("\n")[:-1]
        if not self.__showFunctions:
            definedFunctions = []
        if len(definedFunctions) == 0:
            nodeNameEmptyFile = "_".join(prefix)+"_"+filename
            pathToEmptyFile = "/".join(prefix)+"/"+filename+".py"
            if pathToEmptyFile.startswith("/"):
                pathToEmptyFile = pathToEmptyFile[1:]
            self.__importNames[filename] = nodeNameEmptyFile
            self.__pathNames[pathToEmptyFile] = nodeNameEmptyFile
            graphCode = self.emptyFileStyle
            graphCode += nodeNameEmptyFile.replace("-","")+" [label=\""+filename.replace("-","")+".py\"];\n"
        else:
            nodeNameFilledFile = "cluster_"+"_".join(prefix)+"_"+filename
            pathToFilledFile = "/".join(prefix)+"/"+filename+".py"
            if pathToFilledFile.startswith("/"):
                pathToFilledFile = pathToFilledFile[1:]
            self.__importNames[filename] = nodeNameFilledFile
            self.__pathNames[pathToFilledFile] = nodeNameFilledFile
            graphCode = "subgraph "+nodeNameFilledFile.replace("-","")+" {\n"
            graphCode += self.fileStyle
            graphCode += "label = \""+filename.replace("-","")+".py\";\n"
            classes = subprocess.Popen("grep 'class ' "+path, shell = True, stdout = subprocess.PIPE).stdout.read()
            classes = classes.split("\n")[:-1]
            if len(classes) == 0:
                for d in definedFunctions:
                    graphCode += self.__genCodeFunction(d,filename,prefix)
            else:
                with open(path, "r") as pyFile:
                    pyCode = pyFile.readlines()
                pyCode = self.__filterList(pyCode)
                while len(pyCode) > 0:
                    if "class " in pyCode[0]:
                        className = re.findall(r'^class\ .*:', pyCode[0])[0][6:-1]
                        nodeNameClass = nodeNameFilledFile+"_"+className
                        pathToClass = pathToFilledFile
                        graphCode += "subgraph "+nodeNameClass.replace("-","")+" {\n"
                        graphCode += self.classStyle
                        graphCode += "label = \"class "+className.replace("-","")+"\";\n"
                        pyCode.pop(0)
                        if len(pyCode) == 0:
                            graphCode += "}\n"
                            break
                        foundIndentation, pyCode = self.__getIndentation(pyCode)
                        while len(pyCode) > 0 and foundIndentation+"def " in pyCode[0]:
                            graphCode += self.__genCodeFunction(pyCode[0],filename,prefix+[nodeNameClass])
                            pyCode.pop(0)
                        graphCode += "}\n"
                    else:
                        graphCode += self.__genCodeFunction(pyCode[0],filename,prefix)
                        pyCode.pop(0)
                    
            graphCode += "}\n"
        return graphCode

    def __genCodeFilesInFolder(self,files, prefix):
        graphCode = ""
        for f in files:
            graphCode += self.__genCodeFile(f, prefix)
        return graphCode


    def __genSingleConnection(self, file, importLine):
        importType = None
        listConnections = []
        if re.search(r'.*\ as\ .*', importLine):
            importLine = importLine[ :re.search(r'\ as\ ',importLine).start() ]
        if re.search(r'^\ *import\ .*', importLine):
            importedFile = re.findall(r'import\ .*', importLine)[0][7:]
            importType = "import file"
        elif re.search(r'^\ *from\ .*\ import\ .*', importLine):
            importedFile = re.findall(r'from\ .*\ import', importLine)[0][5:-7]
            importType = "from file import"
            if self.__showFunctions and not re.search(r'.*\ import\ \*', importLine) :
                importedFunctions = re.findall(r'import\ .*', importLine)[0][7:]
                importedFunctions = importedFunctions.replace(" ","").split(",")
                importType = "from file import function"
        else:
            # no match found
            return listConnections

        if importedFile in self.__importNames:
            nameImportedFile = self.__importNames[importedFile]
            nameOriginFile = self.__pathNames["/".join(file)]
            if importType == "from file import function":
                for function in importedFunctions:
                    nameImportedFunction = self.__functionNames[importedFile+":"+function]
                    if not nameOriginFile == nameImportedFunction:
                        listConnections += [nameOriginFile.replace("-","") + self.arrowStyleImportFunction[0] + nameImportedFunction.replace("-","") + " " + self.arrowStyleImportFunction[1] + ";\n"]
            elif importType == "from file import":
                if not nameOriginFile == nameImportedFile:
                    listConnections += [nameOriginFile.replace("-","") + self.arrowStyleFromFile[0] + nameImportedFile.replace("-","") + " " + self.arrowStyleFromFile[1] + ";\n"]
            else:
                if not nameOriginFile == nameImportedFile:
                    listConnections += [nameOriginFile.replace("-","") + self.arrowStyleImportFile[0] + nameImportedFile.replace("-","") + " " + self.arrowStyleImportFile[1] + ";\n"]
            return listConnections
        else:
            # no match found
            return ""
                
    def __genConnectionsFile(self, file):
        listConnections = []
        pathToFile = self.path+"/"+"/".join(file)
        with open(pathToFile) as f:
            fileLines = f.readlines()
        importLines = [line for line in fileLines if "import" in line]
        for importLine in importLines:
            listConnections += self.__genSingleConnection(file, importLine)     
        return listConnections

    def genCodeGraph(self,files, prefix = []):
        processableItems = [f for f in files if len(f) == 1]
        graphCode = self.__genCodeFilesInFolder(processableItems, prefix)
        
        leftoverItems = [f for f in files if not len(f) == 1]

        while len(leftoverItems)> 0:
            nextFolder = leftoverItems[0][0]
            sublistCut = [f[1:] for f in leftoverItems if f[0] == nextFolder]
            newPrefix = prefix + [nextFolder]
            nodeNameFolder = "cluster_"+"_".join(newPrefix)
            pathToFolder = "/".join(newPrefix)
            graphCode += "subgraph "+nodeNameFolder.replace("-","")+" {\n"
            graphCode += self.folderStyle
            graphCode += "label = \""+nextFolder.replace("-","")+"\"\n"
            graphCode += self.genCodeGraph(sublistCut, newPrefix)
            graphCode += "}\n"
            
            leftoverItems = [f for f in leftoverItems if not f[0] == nextFolder]
        return graphCode

    def genConnections(self, files):
        listConnections = []
        for file in files:
            listConnections += self.__genConnectionsFile(file)
        uniqueConnections = list(set(listConnections))
        graphCode = "".join(uniqueConnections)
        return graphCode

    def saveGraph(self, outName = "graph.out", pdfName = "graph.ps"):    
        with open(outName, "w") as out:
            out.write(self.Graph)
        os.system("cat "+outName+" | fdp -Tps -o "+pdfName)
    
