
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject

world_objects = {}

def addToWorld(object):
    world_objects[object.name] = object

class table(IsisObject,IsisVisual,Container,Surface,NoPickup):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics, offsetVec=(0,0,2,0,60,0))
        IsisVisual.__init__(self,model="table/table",scale=0.006)
        NoPickup.__init__(self)
        Container.__init__(self,density=4000)
        Surface.__init__(self, density=4000)

        self.create()
        Container.setup(self)
        Surface.setup(self)

        addToWorld(self)


class fridge(IsisObject, IsisVisual, Container, NoPickup):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics, offsetVec=(0,0,0,0,60,0))
        IsisVisual.__init__(self,model="Fridge/Fridge", scale=0.17)
        NoPickup.__init__(self)
        Container.__init__(self,density=4000)
        self.create()
        self.activeModel.setH(90)
        Container.setup(self)
        self.fullBoxNP.setIntoCollideMask(OBJMASK)
        self.fullBoxNP.setFromCollideMask(OBJMASK)
        
        #freezerDoor
        addToWorld(self)

class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics, offsetVec=(.00,.30,-0.5,0,0,0))
        IsisVisual.__init__(self,model="knife", scale=0.01)
        IsisSpatial.__init__(self, density=25)
        Sharp.__init__(self)

        self.create()
        IsisSpatial.setup(self)

        addToWorld(self)


class toaster(IsisObject, IsisVisual, Container, IsisFunctional):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(.2,0,.6,0,0,0))
        IsisVisual.__init__(self,model="toaster", scale=0.7)
        IsisFunctional.__init__(self)
        Container.__init__(self, density=100)

        # register functional states
        self.registerState("containsToast", [0,1,2])
        self.create()
        Container.setup(self)

        addToWorld(self)

class bread(IsisObject, IsisVisual, Container, IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="slice_of_bread", scale=0.08)
        IsisFunctional.__init__(self)
        Container.__init__(self, density=100)

        self.create()
        Container.setup(self)

        addToWorld(self)

class loaf(IsisObject, IsisVisual, IsisSpatial, Dividable):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="loaf_of_bread", scale=0.2)
        IsisSpatial.__init__(self, density=1000)
        Dividable.__init__(self, bread)

        self.create()
        IsisSpatial.setup(self)

        addToWorld(self)
