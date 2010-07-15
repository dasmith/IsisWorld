from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *


class IsisObject(NodePath):
    """ IsisObject is the base class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, name, physics, offsetVec=(0,0,0,0,0,0), pickupVec=(0,0,0,0,0,0)): 
        # setup the name of the object
        self.name = "IsisObject/"+name+"+"+str(id(self))
        # construct parent NodePath class
        NodePath.__init__(self, self.name)
        # store model offsets 
        self.offsetVec = offsetVec
        self.pickupVec = pickupVec
        # this is the head node that everything is attached to
        self.node = self.node()
        print "VALUE OF NODE", self.node
        # store a pointer to the world manager
        self.physicsManager = physics        
   
    def getName(self):
        return self.name
        
    def getActiveModel(self):
        return self.activeModel

