from pandac.PandaModules import NodePath
from layout_manager import *
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
        if self.getNetTag('heldBy') == '':
            print self.getNetTag('heldBy')
            print "Updating %s" % self.name
            self.model.setPosQuat(self, self.geom.getPosition(), Quat(self.geom.getQuaternion()))
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
            self.heldBy = parent
    def drop(self):
        """ Clears the heldBy variable """
        self.heldBy = None

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
