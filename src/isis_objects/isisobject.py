from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *


class IsisObject(NodePath):
    """ IsisObject is the base class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, name, physics, initialPos=Vec3(0,0,0), offsetVec=Vec3(0,0,-.4)): 
        # setup the name of the object
        self.name = "IsisObject/"+name+"+"+str(id(self))
        # construct parent NodePath class
        NodePath.__init__(self, self.name)
        # store initial and offset positions 
        self.offsetVec = offsetVec
        self.initialPos = initialPos 
        # this is the head node that everything is attached to
        self.node = PandaNode('object-%s' % self.name)
        self.nodePath = render.attachNewNode(self.node)
        self.nodePath.reparentTo(self)
        # store a pointer to the world manager
        self.physicsManager = physics        
   
    def getName(self):
        return self.name


    def call(self, agent, action, object = None):
        try:
            return getattr(self, "action_"+action)(agent, object)
        except AttributeError:
            return None
        except:
            return None
