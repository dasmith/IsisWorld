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
        self.activeModel.setScale(scale)
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
        p1, p2 = self.getTightBounds()
        self.width = abs(p2.getX()-p1.getX())
        self.length = abs(p2.getY()-p1.getY())
        self.height = abs(p2.getZ()-p1.getZ())
        # reset physical model
        self._needToRecalculateScalingProperties = False

    def attachAsPart(self, object):
        """ Attaches another objet to a parent object's exposed joins """
        pass

    def getParts(self):
        """ Returns a list of the labeled sub-node paths that are parts of the model"""
        pass

    def addModel(name,path):
        """ Adds another model state or part to the model path """
        self.models[name]=path

    def changeModel(toName):
        if self.models.has_key(toName):
            print "Changing active model"
            # TODO: blend or play animation depending on kind of transition

    def create(self):
        self.activeModel = loader.loadModel("media/models/"+self.models['default'])
        self.activeModel.setPos(self.initialPos+self.offsetVec)
        self.activeModel.setScale(self.scale)
        self.activeModel.reparentTo(self)
        self.activeModel.setCollideMask(BitMask32.allOff())
        # when models are scaled down dramatically (e.g < 1% of original size), Panda3D represents
        # the geometry non-uniformly, which means scaling occurs every render step and collision
        # handling is buggy.  flattenLight()  circumvents this.
        self.activeModel.flattenLight()
        # adds a pickable tag to allow an agent to view this object
        self.setTag('pickable', 'true')

        # TODO: first destroy physics
        if hasattr(self,'_setupPhysics'):
            self._setupPhysics()

        self._needToRecalculateScalingProperties = True