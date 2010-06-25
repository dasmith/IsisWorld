"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat

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
    """ IsisObject is the base class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, name, model, density = 2000):
        self.name = "IsisObject/"+name+"+"+str(id(self))
        NodePath.__init__(self, self.name)
        self.model = model
        self.model.reparentTo(self)
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
        # private flag to lazily recompute properties when necessary
        self._needToRecalculateScalingProperties = True 
        self.density = density
        self.geom = None# collision geometry for physics
        # initialize dummy variables
        self.width = None
        self.length = None
        self.height = None
        self.weight = None

        self.on_layout = None
        self.in_layout = None

        # organize environments for internal layouts
        self.on_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())
        self.in_layout = self.on_layout
        # adds a pickable tag to allow an agent to view this object
        self.setTag('pickable', 'true')

    def update(self, timeStep=1):
        """ This method is called at each physics step by the Physics Controller
        whenever the object is added as a Kinematic, rather than Dynamic, object""" 
        self.model.setPosQuat(render, self.geom.getPosition(), Quat(self.geom.getQuaternion()))
        return
        quat = self.model.getQuat(self)
        pos = self.model.getPos(self)
        self.geom.setPosition(pos)
        self.geom.setQuaternion(quat)
    
    def rescaleModel(self,scale):
        """ Changes the model's dimensions to a given scale"""
        self.model.setScale(scale)
        self._needToRecalculateScalingProperties = True
  
    def getWeight(self):
        """ Returns the weight of an object, based on its bounding box dimensions
        and its density """
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.weight
    
    def getLength(self):
        """ Returns the length of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.length

    def getWidth(self):
        """ Returns the width of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.width
    
    def getHeight(self):
        """ Returns the height of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.height

    def getDensity(self):
        """ Returns the density of the object"""
        return self.density

    def setDensity(self, density):
        """ Sets the density of the object """
        self.density = density
        self._needToRecalculateScalingProperties = True

    def take(self, parent):
        """ Allows Ralph to pick up a given object """
        if self.weight < 5000:
            self.reparentTo(parent)

    def putOn(self, obj):
        # TODO: requires that object has an exposed surface
        obj.reparentTo(self)
        obj.setPos(self.on_layout.add(obj))

    def putIn(self, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        obj.reparentTo(self)
        obj.setPos(self.in_layout.add(obj))

    def attachAsPart(self, object):
        """ Attaches another objet to a parent object's exposed joins """
        pass

    def getParts(self):
        """ Returns a list of the labeled sub-node paths that are parts of the model"""
        pass
    
    def destroyObject(self):
        # TODO destroy all sub object
        # make some snazzy viz using "explode" ODE method
        pass

    def _recalculateScalingProperties(self):
        """ Internal method for recomputing properties, lazily issued"""
        p1, p2 = self.getTightBounds()
        self.width = abs(p2.getX()-p1.getX())
        self.length = abs(p2.getY()-p1.getY())
        self.height = abs(p2.getZ()-p1.getZ())
        self.weight = self.density*self.width*self.length*self.height
        self._needToRecalculateScalingProperties = False

# Object generators used to instantiate various objects

class IsisObjectGenerator():
    def __init__(self, name, model, scale = 1, density = 2000, offsets = (0, 0, 0)):
        """ This defines a generator object from which instances are derived."""
        self.name = name
        self.model = model
        self.scale = scale
        self.density = density
        #TODO: Automatically center models once they are loaded
        self.offsets = offsets
   
    def generate_instance(self, physicalManager, pos = (0, 0, 0), parent = None):
        """ Generates a new object and adds it to the world"""
        model = loader.loadModel(self.model)
        model.setScale(self.scale)
        # flatten strong causes problem with physics
        #model.flattenLight()

        # add item to Isisworld
        obj = IsisObject(self.name, model, self.density)
        if parent:
            obj.reparentTo(parent)
        obj.setPos(pos)
        model.setPos(self.offsets[0]*obj.width, self.offsets[1]*obj.length, self.offsets[2]*obj.height)
        # add object to physical manager
        geom = physicalManager.addObject(obj)
        # and store its geometry
        obj.geom = geom

        #obj.update()

        return obj


# Main accesser function used to return all available object generators

def load_generators():
    return {"table":IsisObjectGenerator("table", "models3/table/table", .007, 4000),
            "knife":IsisObjectGenerator("knife", "models3/knife", .01, 10000),
            "toaster":IsisObjectGenerator("toaster", "models/kitchen_models/toaster", .7, 5000, (.5, 0, 0)),
            "bread":IsisObjectGenerator("bread", "models/kitchen_models/slice_of_bread", .5, 1000),
            "loaf":IsisObjectGenerator("loaf", "models/kitchen_models/loaf_of_bread", .3, 1000)}




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

    def update(self, timeStep=1):
        """
        Here we update the position of the OdeGeom to follow the
        animated Panda Node. This method is what makes our object
        a kinematic one.
        """
        #self.NP.setPosQuat(render, self.body.getPosition(), Quat(self.body.getQuaternion()))
'''
