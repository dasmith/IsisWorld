
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject

from direct.interval.IntervalGlobal import *

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
        #self.fullBoxNP.setIntoCollideMask(OBJMASK)
        #self.fullBoxNP.setFromCollideMask(OBJMASK)
        self.state = "closed"
        #freezerDoor
        addToWorld(self)
        fd = self.activeModel.find("**/freezerDoor*")
        fd.hide()
        self.door = self.activeModel.find("**/fridgeDoor*")
        #self.door.place()
        self.door.setPos(-0.7,.4,.5)

    def setState(self,state):
        self.state = state

    def action__open(self, agent, directobj):
        print "Select method called"
        if self.state == "closed":
            Sequence(
                Func(self.setState, "closing"),
                LerpHprInterval(self.door, 0.5, Vec3(125, 0, 0)),
                Func(self.setState, "close"),
            ).start()
        elif self.state == "opened":
            Sequence(
                Func(self.setState, "opening"),
                LerpHprInterval(self.door, 0.5, Vec3(0, 0, 0)),
                Func(self.setState, "opened"),
            ).start()

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
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(.4,0,.6,0,0,0))
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
