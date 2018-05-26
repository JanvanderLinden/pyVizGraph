import pyVizGraphClass
import sys
import os

graph = pyVizGraphClass.Graph(path=sys.argv[1], showFunctions=True)
graph.saveGraph()
os.system("okular graph.ps")
