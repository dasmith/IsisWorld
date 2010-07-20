
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject
from layout_manager import SlotLayout

from direct.interval.IntervalGlobal import *

world_objects = {}

def addToWorld(object):
    world_objects[object.name] = object

class table(IsisObject,IsisVisual,Container,Surface,NoPickup):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="table/table",scale=0.006)
        self.create()

        Container.__init__(self, density=4000)
        Container.setup(self)
        Surface.__init__(self, density=4000)
        Surface.setup(self)

        NoPickup.__init__(self)

        addToWorld(self)


class fridge(IsisObject, IsisVisual, Container, NoPickup):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(0,0,0,90,0,0))
        IsisVisual.__init__(self,model="Fridge/Fridge", scale=0.17)
        self.create()

        Container.__init__(self,density=4000)
        Container.setup(self)
        self.in_layout = SlotLayout([(0, 0, .5), (0, 0, 1),(0, 0, 1.5)])

        #self.fullBoxNP.setIntoCollideMask(OBJMASK)
        #self.fullBoxNP.setFromCollideMask(OBJMASK)
        self.state = "closed"

        #freezerDoor
        fd = self.activeModel.find("**/freezerDoor*")
        fd.setPos(-.6, -.55, 1.65)
        self.door = self.activeModel.find("**/fridgeDoor*")
        self.door.setPos(-0.6,-.55,.72)

        NoPickup.__init__(self)

        addToWorld(self)

    def setState(self,state):
        self.state = state

    def action__open(self, agent, directobj):
        print "Select method called"
        if self.state == "closed":
            Sequence(
                Func(self.setState, "opening"),
                LerpPosHprInterval(self.door, 0.5, Vec3(-2.3, 1.35, .72), Vec3(-125, 0, 0)),
                Func(self.setState, "opened"),
            ).start()
        elif self.state == "opened":
            Sequence(
                Func(self.setState, "closing"),
                LerpPosHprInterval(self.door, 0.5, Vec3(-.6, -.55, .72), Vec3(0, 0, 0)),
                Func(self.setState, "closed"),
            ).start()

class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,pickupVec=(0,.15,0,0,75,0))
        IsisVisual.__init__(self,model="knife", scale=0.01)
        self.create()

        IsisSpatial.__init__(self, density=25)
        IsisSpatial.setup(self)

        Sharp.__init__(self)

        addToWorld(self)


class toaster(IsisObject, IsisVisual, Container, Cooker):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(.5,.16,.19,-8,0,0))
        IsisVisual.__init__(self,model="toaster", scale=0.7)
        self.create()

        Container.__init__(self, density=100)
        Container.setup(self)
        self.on_layout = SlotLayout([(.3, .1, .2), (.3, -.1, .2)])

        Cooker.__init__(self)
        #register functional states
        self.registerState("containsToast", [0,1,2])

        addToWorld(self)

class bread(IsisObject, IsisVisual, Container, IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(0,0,-.1,0,-120,-20),pickupVec=(-.125,.225,0,0,-125,0))
        IsisVisual.__init__(self,model={"default":"slice_of_bread", "cooked":"piece_of_toast"}, scale=0.5)
        self.create()

        Container.__init__(self, density=100)
        Container.setup(self)

        IsisFunctional.__init__(self)

        addToWorld(self)

class loaf(IsisObject, IsisVisual, IsisSpatial, Dividable):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(.00144,0,0,0,0,0))
        IsisVisual.__init__(self,model="loaf_of_bread", scale=0.2)
        self.create()

        IsisSpatial.__init__(self, density=1000)
        IsisSpatial.setup(self)

        Dividable.__init__(self, bread)

        addToWorld(self)