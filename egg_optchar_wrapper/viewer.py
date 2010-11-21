import os
import sys
import direct.directbase.DirectStart

if __name__ == '__main__':
    print "sys.argv: ", sys.argv
    print "len(sys.argv) ", len(sys.argv)
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using panda.egg as the default."
        modelName = "panda.egg"
    else:
        modelName = sys.argv[1]
    viewCmd = 'pview %s' % modelName
    
    # Doesn't actually display?
    #panda = render.attachNewNode("panda.egg")
    
    #os.system(viewCmd)
    inp = raw_input("What do you want to do?")
    print "You inputted ", inp