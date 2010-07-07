from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *
from layout_manager import *

class IsisVisual():
    """ This is the base class responsible for handling all of the visual aspects of an object
    in IsisWorld, including all of the handling of visual features (scaling, colors, textures),
    and models (animations, exposing parts).
    
    It is the first class instantiated because the self.activeModel is what is used in the other
    object classes: IsisSpatial and IsisFunctional."""

    def __init__(self, model=None, scale=1.0):
        # keep a dictionary mapping model names to paths 
        self.models = {}
        
        # define default model or override
        if model == None:
            self.models['default'] = "box"
        elif isinstance(model,dict):
            # accept a dictionary with a 'default' key of models
            self.models = model
            if not self.models.has_key("default"):
                raise "Error: default model needed for IsisVisual object"
        elif isinstance(model,str):
            self.models = {}
            self.models['default'] = model

        # set the scale of the object
        self.scale = scale

        # private flag to lazily recompute properties when necessary
        self._needToRecalculateScalingProperties = True 
        
        # initialize dummy variables
        self.width = None
        self.length = None
        self.height = None
        self.weight = None

        self.on_layout = None
        self.in_layout = None

    def rescaleModel(self,scale):
        """ Changes the model's dimensions to a given scale"""
        self.activeModel.setScale(scale)
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
        # reset physical model
        self._needToRecalculateScalingProperties = False

    def addModel(name,path):
        """ Adds another model state or part to the model path """
        self.models[name]=path

    def changeModel(toName):
        if self.models.has_key(toName):
            print "Changing active model"
            # TODO: blend or play animation depending on kind of transition

    def create(self):
        print "Called for IsisVisual ", self.name
        self.activeModel = loader.loadModel("media/models/"+self.models['default'])
        self.activeModel.setPos(self.initialPos+self.offsetVec)
        self.activeModel.setScale(self.scale)
        self.activeModel.reparentTo(self.nodePath)
        self.activeModel.setCollideMask(BitMask32.allOff())
        # when models are scaled down dramatically (e.g < 1% of original size), Panda3D represents
        # the geometry non-uniformly, which means scaling occurs every render step and collision
        # handling is buggy.  flattenLight()  circumvents this.
        self.activeModel.flattenLight()
        # organize environments for internal layouts
        self.on_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())
        self.in_layout = self.on_layout
        # adds a pickable tag to allow an agent to view this object
        self.setTag('pickable', 'true')

        # TODO: first destroy physics
        if hasattr(self,'_setupPhysics'):
            self._setupPhysics()

        self._needToRecalculateScalingProperties = True 
