"""  Object Loader for IsisWorld Simulator """
import sys, re, time
from random import randint, random
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat
from isis_objects.generators import * 

def instantiate_isisobject(classname, physics):
    """ Instantiates an IsisObject as defined in a class in the "generators.py" file.
      - classname:  the name of the IsisObject type
      - physics: a pointer to the worldManager, required for adding collision geometries later
    """
    print "Creating an instance of %s" % classname
    __import__("src.isis_objects.generators")
    return getattr(sys.modules["src.isis_objects.generators"], classname)(name=classname,physics=physics)

def load_objects_file(file):
    return map(lambda x: x.strip(), open(file,'r').readlines()) 

def load_objects(file, renderParent, physicsManager):
    # add each object to the world
    world_objects = {}
    context = {}

    for instruction in load_objects_file(file):
        print instruction
        if len(instruction) == 0 or instruction[0] == "#":
            continue
        item = instruction.split("\t")[0]
        if len(instruction.split("\t")) > 1:
            parent = renderParent
            loc = None
            rot = (0, 0, 0)
            prep = None
            name = None

            for option in instruction.split("\t")[1:]:
                key,val = option.split(" ")
                if key == "named":
                    name = val
                elif key == "at":
                    x,y,z = val.split(",")
                    loc = (float(x), float(y), float(z))
                elif key == "oriented":
                    h,p,r = val.split(",")
                    rot = (float(h), float(p), float(r))
                elif val in context:
                    parent = context[val]
                    prep = key
            print item
            obj = instantiate_isisobject(item, physicsManager) 
            obj.create()
            print "Creating object %s" % (obj.name)
            obj.setHpr(rot)
            if prep == "on":
                parent.putOn(obj)
            elif prep == "in":
                parent.putIn(obj)
            else:
                obj.reparentTo(renderParent)
            if loc:
                obj.setPos(obj, loc)
            world_objects[obj.name] = obj
            if name:
               context[name] = obj
            context[item] = obj

    print world_objects
    return world_objects
