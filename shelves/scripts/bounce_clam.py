import sys

for i in sys.modules.keys()[:]:
    if (i.startswith("clam")
            or i.startswith("squirrel")
            or i.startswith("libClarisse")):
        del(sys.modules[i])
