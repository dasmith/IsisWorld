from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *


class IsisObject(NodePath):
    """ IsisObject is the decorator class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, physics): 
        # store pointer to world manager
        self.physics = physics
        
        # generate a unique name for the object, warning, unique id uses GENERATORS ID
        self.name = "IsisObject/"+self.generator.__class__.__name__+"+"+str(id(self))
        
        # construct parent IsisObject class
        IsisObject.__init__(self, self.name)
        
        self.node = self.node()
        # store pointer to IsisObject subclass
        self.setPythonTag("isisobj", self)
        # bind worldmanager pointer to instance
        self.physics = physics
        # store model offsets 
        if not hasattr(self, 'offsetVec'):
            self.offsetVec = (0,0,0,0,0,0)
        if not hasattr(self, 'pickupVec'):
            self.pickupVec = (0,0,0,0,0,0)

        if not hasattr(self,'physics'):
            raise "Error: %s missing self.physics" % self.name

        superclasses =  map(lambda x: [x,hasattr(x, 'priority') and x.priority or 101], self.generator.__bases__)
        # call __init__ on all parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if sc != "NodePath":
                sc.__init__(self)
            print sc, rank
        # call setup() on all appropriate parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if hasattr(sc,'setup'):
                sc.setup(self)
        if hasattr(self,'setup'):
            self.setup()

    def getName(self):
        return self.name
        
    def getActiveModel(self):
        return self.activeModel

