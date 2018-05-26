# pyVizGraph

use this tool to graphically vizualize a python software project / etc.

## requirements

the vizualization relies on the installation of graphviz and its gts library
run
```
sudo apt install libgts-dev
sudo pkg-config --libs gts
sudo pkg-config --cflags gts
```
download `graphviz-2.40.1.tar.gz` from [here](https://www.graphviz.org/download/)
extract
run
```
sudo ./configure --with-gts --prefix install/path
sudo make
sudo make install
```
add the files in `bin` to the executables on your system

## how to use
```
import pyVizGraphClass
import sys
import os

graph = pyVizGraphClass.Graph(path=sys.argv[1], showFunctions=True)
graph.saveGraph()
os.system("okular graph.ps")
```

generate the Graph with initialization of class `Graph`
    takes `path` to repository as input (should not end with `/`)
    boolean `showFunctions`: show only file structure or files and functions

save graph with `saveGraph` function
    takes name as voluntary argument
    always saves as `.ps` and raw graph as `.out` files



    
