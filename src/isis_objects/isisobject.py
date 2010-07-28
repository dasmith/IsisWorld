from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *


class IsisObject(NodePath):
    """ IsisObject is the decorator class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, generator): 
        # store pointer to generator class
        self.generator = generator
    
    def __call__(self, physics):
        
        # generate a unique name for the object, warning, unique id uses GENERATORS ID
        name = "IsisObject/"+self.generator.__class__.__name__+"+"+str(id(self))
        # make instance of generator 
        self.instance = self.generator(name)
        self.instance.node = self.instance.node()
        # store pointer to IsisObject subclass
        self.instance.setPythonTag("isisobj", self.instance)
        # bind worldmanager pointer to instance
        self.instance.physics = physics
        

        # store model offsets 
        if not hasattr(self.instance, 'offsetVec'):
            self.instance.offsetVec = (0,0,0,0,0,0)
        if not hasattr(self, 'pickupVec'):
            self.instance.pickupVec = (0,0,0,0,0,0)

        if not hasattr(self.instance,'physics'):
            raise "Error: %s missing self.physics" % self.instance.name

        superclasses =  map(lambda x: [x,hasattr(x, 'priority') and x.priority or 101], self.generator.__bases__)
        # call __init__ on all parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if sc != "NodePath":
                sc.__init__(self.instance)
            print sc, rank
        # call setup() on all appropriate parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if hasattr(sc,'setup'):
                sc.setup(self.instance)
        if hasattr(self.instance,'setup'):
            self.instance.setup()

    def getName(self):
        return self.name
        
    def getActiveModel(self):
        return self.activeModel

