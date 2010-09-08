from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
#from ..physics.panda.manager import *


class IsisObject(NodePath):
    """ IsisObject is the decorator class for all visible objects in IsisWorld, other
    than sky, house, ground and agents.
    
    This iterates through the parent classes and initializes them, then calls
    their setup() method, if they have one defined, and then calls the afterSetup()
    method on just the isisobject generator."""
    priority = 0
    
    
    def  __init__(self,name=1):
        # generate a unique name for the object, warning, unique id uses GENERATORS ID
        self.name = "IsisObject/"+self.__class__.__name__+"+"+str(id(self))
        # reference to the layout parent
        self.layout = None
        
        NodePath.__init__(self,self.name)
        # store pointer to IsisObject subclass
        self.setPythonTag("isisobj", self)
        # store model offsets 
        if not hasattr(self, 'offsetVec'):
            self.offsetVec = (0,0,0,0,0,0)
        if not hasattr(self, 'pickupVec'):
            self.pickupVec = (0,0,0,0,0,0)

        if not hasattr(self,'physics'):
            raise "Error: %s missing self.physics" % self.name
        
        superclasses =  map(lambda x: [x,hasattr(x, 'priority') and x.priority or 101], self.__class__.__bases__)
        # call __init__ on all parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if sc.__name__ != "IsisObject":
                sc.__init__(self)
        # call generator's setup method first
        if hasattr(self,'setup'):
            self.setup()
        # call setup() on all appropriate parent classes
        for sc, rank in sorted(superclasses, key=lambda x: x[1]):
            if hasattr(sc,'setup'):
                sc.setup(self)
        # call generator's post-setup function too
        if hasattr(self,'afterSetup'):
            self.afterSetup()

        # register object in main:  this is used for 
        # destroying all of the initialized objects later
        self.physics.main.objects.append(self)

    @classmethod
    def setPhysics(cls,physics):
        """ This method is set in src.loader when the generators are loaded
        into the namespace.  This frees the environment definitions (in 
        scenario files) from having to pass around the physics parameter 
        that is required for all IsisObjects """
        cls.physics = physics

    def setLayout(self, l):
        self.layout = l

    def getName(self):
        return self.name[11:]
        
    def getActiveModel(self):
        return self.activeModel
        
    def removeFromWorld(self):
        #self.physics.removeObject(self)
        #self.destroy()
        if self.activeModel:
            self.activeModel.removeNode()
            self.removeNode()
        del self.activeModel
        # destroy physics component
        
