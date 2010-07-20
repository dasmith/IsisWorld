from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

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
        self._needToRecalculateScalingProperties = False
        
        # initialize dummy variables
        self.width = None
        self.length = None
        self.height = None

    def rescaleModel(self,scale):
        """ Changes the model's dimensions to a given scale"""
        self.activeModel.setScale(scale, scale, scale)
        self.scale = scale
        self._needToRecalculateScalingProperties = True

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

    def _recalculateScalingProperties(self):
        """ Internal method for recomputing properties, lazily issued"""
        p1, p2 = self.activeModel.getTightBounds()
        self.width = abs(p2.getX()-p1.getX())
        self.length = abs(p2.getY()-p1.getY())
        self.height = abs(p2.getZ()-p1.getZ())
        # reset physical model
        self._needToRecalculateScalingProperties = False

    def attachAsPart(self, object):
        """ Attaches another object to a parent object's exposed joins """
        pass

    def getParts(self):
        """ Returns a list of the labeled sub-node paths that are parts of the model"""
        pass

    def getModelNode(self):
        return self.activeModel

    def addModel(self, name, path):
        """ Adds another model state or part to the model path """
        self.models[name] = loader.loadModel("media/models/"+path)
        self.models[name].setPosHpr(*self.offsetVec)
        self.models[name].setScale(self.scale)
        self.models[name].setCollideMask(BitMask32.allOff())

    def changeModel(self, toName):
        if self.models.has_key(toName):
            print "Changing active model"
            # TODO: blend or play animation depending on kind of transition
            if self.activeModel:
                self.activeModel.detachNode()
            self.activeModel = self.models[toName]
            self.activeModel.reparentTo(self)
            # when models are scaled down dramatically (e.g < 1% of original size), Panda3D represents
            # the geometry non-uniformly, which means scaling occurs every render step and collision
            # handling is buggy.  flattenLight()  circumvents this.
            self.activeModel.flattenLight()

    def create(self):
        for key in self.models:
            self.addModel(key, self.models[key])
        self.activeModel = None;
        self.changeModel('default')
        # adds a pickable tag to allow an agent to view this object
        self.setTag('pickable', 'true')

        self._needToRecalculateScalingProperties = True