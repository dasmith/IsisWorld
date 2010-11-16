from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

class IsisVisual():
    """ This is the base class responsible for handling all of the visual aspects of an object
    in IsisWorld, including all of the handling of visual features (scaling, colors, textures),
    and models (animations, exposing parts).
    
    It is the first class instantiated because the self.activeModel is what is used in the other
    object classes: IsisSpatial and IsisFunctional."""

    priority = 2
    
    def __init__(self):
        # keep a dictionary mapping model names to paths 
        self.models = {}
        # define default model or override
        if not hasattr(self,'model'):
            self.models['default'] = "box"
        elif isinstance(self.model,dict):
            # accept a dictionary with a 'default' key of models
            self.models = self.model
            if not self.models.has_key("default"):
                raise Exception("Error: default model needed for IsisVisual object")
        elif isinstance(self.model,str):
            self.models = {}
            self.models['default'] = self.model
        else:
            # assume model is a generated model
            self.models['default'] = self.model

        # set the scale of the object
        if not hasattr(self,'scale'):
            self.scale = 1

        # private flag to lazily recompute properties when necessary
        self._needToRecalculateScalingProperties = False
    
    def setPosition(self,pos):
        # set position of nodepath
        self.setPos(pos)
        # set position of physics -- doesn't need argument, it gets it from activeModel
        self.setGeomPos(pos)
        
        
    def setRotation(self,hpr):
        self.setHpr(hpr)
        self.synchPosQuatToNode()

    def rotateAlongX(self,x):
        """ Rotates the model and the ODE geom along the X axis"""
        self.setH(self.getH()+x)
        self.synchPosQuatToNode()
        self._needToRecalculateScalingProperties = True
        
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

    def get_middle(self):
        """ Returns the middle of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return Vec3((self.width, self.height,0))


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
        """ Adds another model state or part to the model path.
        This is set to a string to the egg file (without the .egg) 
        and is loaded later by changeModel """
        self.models[name] = path
        #self.models[name].setScale(self.scale)
        #self.models[name].setCollideMask(BitMask32.allOff())

    def changeModel(self, changeToKey):
        """ Given, changeToKey, containing the key of the self.models dict, this loads
        the activeModel.
        
        TODO: improve so that models can have their own scale. Generalize with separate Models class."""
        if self.models.has_key(changeToKey):
            # TODO: blend or play animation depending on kind of transition
            if hasattr(self,'activeModel') and self.activeModel:
                #self.activeModel.detachNode()
                self.activeModel.remove()
            self.activeModel = loader.loadModel("media/models/"+self.models[changeToKey])
            self.activeModel.setScale(self.scale)
            self.activeModel.setPosHpr(*self.offset_vector)
            self.activeModel.setCollideMask(BitMask32.allOff())
            self.activeModel.reparentTo(self)

            # when models are scaled down dramatically (e.g < 1% of original size), Panda3D represents
            # the geometry non-uniformly, which means scaling occurs every render step and collision
            # handling is buggy.  flattenLight()  circumvents this.
            self.activeModel.flattenLight()
        else:
            raise Exception("Error in %s.changeModel() -- cannot find model %s" % (self.name, changeToKey))

    def setup(self):
        if not hasattr(self,'staticModel'):
            self.changeModel('default')
            # adds a pickable tag to allow an agent to view this object
            self.setTag('pickable', 'true')
        else:
            self.activeModel.reparentTo(self)
        self._needToRecalculateScalingProperties = True