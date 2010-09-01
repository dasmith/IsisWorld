from pandac.PandaModules import *
#from pandac.PandaModules import Vec3, BitMask32 
from ..physics.ode.odeWorldManager import *
from ..physics.ode.pickables import *

from direct.controls.ControlManager import CollisionHandlerRayStart
from layout_manager import *


class Container():
    
    def __init__(self):
        pass




class SpatialPickable(pickableObject):
    priority = 3

    def __init__(self):
        if not hasattr(self,'category'):
            self.category = "static"
        
        pickableObject.__init__(self,"box",0.5)
        self.geomSize = (1.0,1.0,1.0)
        self.friction = 1.0

        #self.mapObjects["kinematics"].append(self)
    
    def setup(self):
        
        self.physics.addObjectToWorld(self,'dynamics')
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        print "Creating:", self.name
        self.setupGeomAndPhysics(self.physics, pos, quat)
        self.showCCD = False


class SpatialPickableBox(pickableObject):

    def __init__(self):
        # weight = 0.5
        pickableObject.__init__(self, "box", 0.5)
        self.friction = 1.0      
        self.showCCD = False

    def setup(self):
        self.geomSize =self.physics.extractSizeForBoxGeom(self.activeModel)
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        self.setupGeomAndPhysics(self.physics, pos, quat)

class SpatialPickableBall(pickableObject):
    def __init__(self):
        pickableObject.__init__(self, "ball", 0.5)
        self.modelPath = "./graphics/models/ball.egg"
        self.shape = "sphere"
        self.showCCD = False
        self.friction = 3.0

    def setup(self):
        lcorner, ucorner =self.activeModel.getTightBounds()
        radius = min(ucorner[0]-lcorner[0],ucorner[1]-lcorner[1])/2.0
        self.geomSize = radius
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        self.setupGeomAndPhysics(self.physics, pos, quat)




class SpatialStaticBox(staticObject):
    priority = 3

    def __init__(self):
        staticObject.__init__(self, self.physics)


    def setup(self):
        self.setBoxGeomFromNodePath(self.activeModel)
        self.state = "vacant"
        self.physics.addObject(self)
        self.physics.main.mapObjects["static"].append(self)

class SpatialStaticTriMesh(staticObject):
    priority = 5
    def __init__(self):
        staticObject.__init__(self,self.physics)
    
    def setup(self):
        self.setTrimeshGeom(self.activeModel)
        #self.setCatColBits("environment")

        self.physics.addObject(self)
        self.physics.main.mapObjects["static"].append(self)

