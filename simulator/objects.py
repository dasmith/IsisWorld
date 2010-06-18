"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath


# Various layout managers used to generate coordinates for placing objects

class LayoutManager():
    def add(self, obj):
        return (0, 0, 0)

class HorizontalGridLayout(LayoutManager):
    """Arranges objects in rows within the given area"""
    def __init__(self, area, height, padw = .05, padh = .05):
        self.w, self.h = area
        self.z = height
        self.px, self.py = (0, 0)
        self.maxh = 0
        self.padw = padw
        self.padh = padh
    def add(self, obj):
        ow = obj.width+self.padw
        oh = obj.length+self.padh
        if self.px+ow > self.w:
            self.py += self.maxh
            self.px = 0
            self.maxh = 0
            if self.py+oh > self.h:
                return (0, 0, self.z)
        x = self.px
        self.px += ow
        if oh > self.maxh:
            self.maxh = oh
        return (x-(self.w-obj.width)/2.0, self.py-(self.h-obj.height)/2.0, self.z)



# Object class definitions defining methods inherent to each object type

class IsisObject(NodePath):
    def  __init__(self, name, model, density = 2000):
        self.name = "IsisObject/"+name+str(id(self))
        NodePath.__init__(self, self.name)
        self.model = model
        self.model.reparentTo(self)

        p1, p2 = self.getTightBounds()
        self.width = abs(p2.getX()-p1.getX())
        self.length = abs(p2.getY()-p1.getY())
        self.height = abs(p2.getZ()-p1.getZ())
        self.weight = density*self.width*self.length*self.height

        self.on_layout = HorizontalGridLayout((self.width, self.length), self.height)
        self.in_layout = self.on_layout
    def take(self, parent):
        if self.weight < 5000:
            self.reparentTo(parent)
    def putOn(self, obj):
        obj.reparentTo(self)
        obj.setPos(self.on_layout.add(obj))
    def putIn(self, obj):
        obj.reparentTo(self)
        obj.setPos(self.in_layout.add(obj))



# Object generators used to instantiate various objects

class IsisObjectGenerator():
    def __init__(self, name, model, scale = 1, density = 2000, offsets = (0, 0, 0)):
        """ This defines a generator object from which instances are derived."""
        self.name = name
        self.model = model
        self.scale = scale
        self.density = density
        #TO-DO: Automatically center models once they are loaded
        self.offsets = offsets
   
    def generate_instance(self, pos = (0, 0, 0), parent = None):
        """ Generates a new object and adds it to the world"""
        model = loader.loadModel(self.model)
        model.setScale(self.scale)
        model.flattenStrong()

        obj = IsisObject(self.name, model, self.density)
        if parent:
            obj.reparentTo(parent)
        obj.setPos(pos)
        model.setPos(self.offsets[0]*obj.width, self.offsets[1]*obj.length, self.offsets[2]*obj.height)

        return obj


# Main accesser function used to return all available object generators

def load_generators():
    return {"table":IsisObjectGenerator("table", "models3/table/table", .007, 4000),
            "knife":IsisObjectGenerator("knife", "models3/knife", .01, 10000),
            "toaster":IsisObjectGenerator("toaster", "models/kitchen_models/toaster", .7, 5000, (.5, 0, 0)),
            "bread":IsisObjectGenerator("bread", "models/kitchen_models/slice_of_bread", .5, 1000),
            "loaf":IsisObjectGenerator("loaf", "models/kitchen_models/loaf_of_bread", .3, 1000)}






"""    Material	Density (kg/m^3)
    Balsa wood	120
    Brick	2000
    Copper	8900
    Cork	250
    Diamond	3300
    Glass	2500
    Gold	19300
    Iron	7900
    Lead	11300
    Styrofoam	100
"""
'''
    def __repr__(self):
        return "%s(name=%r, posHpr=%r, states=%r, models=%r, scale=%r, density=%r)" % (self.__class__.__name__, self.name, self.posHpr, self.states, self.models, self.scale, self.density)


        self.state = "close"
        self.speed = 15

        self.worldManager = worldManager
        self.models = models
        self.name = name
        self.NP = activeModel
        self.ode = None
        self.InitialHpr = self.NP.getHpr()

        #self.worldManager.addBox(self.NP, density, self, self.select, is_kinematic=True)
        #if self.data.name == "knife": self.NP.place()
        
        
    def select(self, character, direction):
        if self.state == "close":
            self.open(self.NP.getQuat(render).xform(direction).getY())
        elif self.state == "open":
            self.close()

    def close(self):
        """
        Here we use the Panda Sequence and Interval to close the door.
        Notice the transitional state *ing during the sequence.
        Without it it would be possible to start opening/closing
        the door during animation.
        """
        #closeInterval = LerpHprInterval(self.doorNP, self.speed, self.hpr)
        #Sequence(
        #        Func(self.changeState, "closing"),
        #        closeInterval,
        #        Func(self.changeState, "close"),
        #).start()

    def open(self, dir):
        """
        The direction is here to make sure the door opens from the character
        instead of to it. This might be a little unrealistic (typpically door
        open one way), but it tends to give better results.
        """
        if dir > 0:
            newH = -85.0
        else:
            newH = 85.0

        """
        Calculate the new heading for the door.
        """
        #newH += self.doorNP.getH()

        """
        And run the sequence to close it.
        """
        #Sequence(
        #        Func(self.changeState, "opening"),
        #        LerpHprInterval(self.doorNP, self.speed, Vec3(newH, 0, 0)),
        #        Func(self.changeState, "open"),
        #).start()

    def changeState(self, newState):
        self.state = newState

    def nodepath(self):
        return self.NP

    def getPosQuat(self):
        return self.NP.getPosQuat()

    def update(self, timeStep):
        """
        Here we update the position of the OdeGeom to follow the
        animated Panda Node. This method is what makes our object
        a kinematic one.
        """
        #self.NP.setPosQuat(render, self.body.getPosition(), Quat(self.body.getQuaternion()))
'''