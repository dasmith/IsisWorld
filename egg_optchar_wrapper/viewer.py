import os
import sys

if __name__ == '__main__':
    print "sys.argv: ", sys.argv
    if len(sys.argv) != 2:
        "Please specify a model to show. Using panda.egg as the default."
        modelName = "panda.egg"
    else:
        modelName = sys.argv[1]
    viewCmd = 'pview %s' % modelName
    os.system(viewCmd)