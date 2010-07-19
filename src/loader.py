"""  Object Loader for IsisWorld Simulator """
import sys
from isis_objects.generators import world_objects

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

def load_objects(file, renderParent, physicsManager, layoutManager = None):
    # add each object to the world
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
            print "Creating object %s" % (obj.name)
            print "Dimensions: w=%f, l=%f, h=%f" % (obj.getWidth(), obj.getLength(), obj.getHeight())
            obj.setHpr(rot)
            if prep == "on":
                if parent.call(None, "put_on", obj) != "success":
                    obj.reparentTo(renderParent)
                    x, y, z = parent.activeModel.getPos(renderParent)
                    obj.setPos(x, y, z+1)
            elif prep == "in":
                if parent.call(None, "put_in", obj) != "success":
                    obj.reparentTo(renderParent)
                    x, y, z = parent.activeModel.getPos(renderParent)
                    obj.setPos(x, y, z+1)
            else:
                obj.reparentTo(renderParent)
                if layoutManager:
                    obj.setPos(layoutManager.add(obj))
            if loc:
                obj.setPos(obj, loc)
            if name:
               context[name] = obj
            context[item] = obj

    print world_objects
    return world_objects
