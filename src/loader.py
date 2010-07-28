"""  Object Loader for IsisWorld Simulator """
import sys
#from isis_objects.generators import world_objects

def instantiate_isisobject(classname, physics):
    """ Instantiates an IsisObject as defined in a class in the "generators.py" file.
      - classname:  the name of the IsisObject type
      - physics: a pointer to the worldManager, required for adding collision geometries later
    """
    # load the class modules from the generators file into the namespace
    __import__("src.isis_objects.generators")
    # create an instance
    newInstance = getattr(sys.modules["src.isis_objects.generators"], classname)(physics)
    # attach the physics manager pointer to the instance
    #newInstance.physics = physics
    return newInstance

def load_objects_file(file):
    return map(lambda x: x.strip(), open(file,'r').readlines()) 

def load_objects(file, renderParent, physicsManager, layoutManager = None):
    # add each object to the world
    context = {}

    for instruction in load_objects_file(file):
        if len(instruction) == 0 or instruction[0] == "#":
            continue

        item = instruction.split("\t")[0]
        print item
        parent = renderParent
        loc = (0, 0, 0)
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
        obj = instantiate_isisobject(item, physicsManager)
        loc = (loc[0]+obj.getX(), loc[1]+obj.getY(), loc[2]+obj.getZ())
        rot = (rot[0]+obj.getH(), rot[1]+obj.getP(), rot[2]+obj.getR())
        obj.setPosHpr(0, 0, 0, 0, 0, 0)

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

        obj.setPosHpr(obj, loc, rot)
        if name:
           context[name] = obj
        context[item] = obj

    return True