from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject
from layout_manager import SlotLayout

from direct.interval.IntervalGlobal import *


class table(IsisObject,IsisVisual,Container,Surface,NoPickup):

    def  __init__(self, physics):
        # store pointer to world manager
        self.physics = physics
        self.offsetVec = offsetVec=(0,0,0,0,0,0)
        self.model = "table/table"
        self.scale=0.006
        self.density = 4000

        IsisObject.__init__(self)

        self.setH(180)


class fridge(IsisObject, IsisVisual, Container, NoPickup):
    
    def  __init__(self, physics):
        # store pointer to world manager
        self.physics = physics
        self.model={'default':"Fridge/Fridge"}
        self.scale=0.17
        self.density = 4000
        self.state = "closed"

        IsisObject.__init__(self)

        self.in_layout = SlotLayout([(0, 0, .5), (0, 0, 1),(0, 0, 1.5)])
        
    def setup(self):
        fd = self.activeModel.find("**/freezerDoor*")
        fd.setPos(-.56, .6, 1.65)
        self.door = self.activeModel.find("**/fridgeDoor*")
        self.door.setPos(-0.56, .6, .72)
        self.setH(0)

    def setState(self,state):
        self.state = state

    def action__open(self, agent, directobj):
        print "Select method called"
        if self.state == "closed":
            Sequence(
                Func(self.setState, "opening"),
                LerpPosHprInterval(self.door, 0.5, Vec3(.45, 2.4, .72), Vec3(-90, 0, 0)),
                Func(self.setState, "opened"),
            ).start()
        elif self.state == "opened":
            Sequence(
                Func(self.setState, "closing"),
                LerpPosHprInterval(self.door, 0.5, Vec3(-.56, .6, .72), Vec3(0, 0, 0)),
                Func(self.setState, "closed"),
            ).start()


class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def  __init__(self, physics): 
        # store pointer to world manager
        self.physics = physics
        self.offsetVec = (0,0,0.3,0,0,0)
        self.pickupVec = (0,.15,0,0,75,0)
        self.model="knife"
        self.scale=0.01
        self.density = 25
        IsisObject.__init__(self)

class toaster(IsisObject, IsisVisual, Container, Cooker):
    
    def __init__(self, physics):
        self.physics = physics
        ######### Base Variables ##########
         # visual offset for the model's position and rotation
        self.offsetVec = (.5,.16,.19,-8,0,0)
        
        ######## Visual Parameters ###############
        # store a model, either as a string or a dictionary
        self.model = "toaster"
        self.scale = 0.7
        ######## Spatial Parameters ##############
        self.density = 100
        self.on_layout = SlotLayout([(.3, .1, .2), (.3, -.1, .2)])

        ######## Functional Parameters ############
        self.cook_in = True
        self.cook_on = False
        
        self.registerState("containsToast", [0,1,2])
        IsisObject.__init__(self)

class bread(IsisObject, IsisVisual, Container, Cookable):

    def  __init__(self, physics): 
        # store pointer to world manager
        self.physics = physics

        self.offsetVec = (0,0,-.1,0,-120,-20)
        self.pickupVec=(-.125,.225,0,0,-125,0)
        self.model={"default":"slice_of_bread", "toast":"piece_of_toast"}
        self.scale = 0.5
        
        self.density = 200
        
        self.cookableCookedModel = "toast"
        IsisObject.__init__(self)

class loaf( IsisObject, IsisVisual, IsisSpatial, Dividable):

    def  __init__(self, physics): 
        # store pointer to world manager
        self.physics = physics
        self.offsetVec = (.00144,0,0.3,0,0,0)
        
        self.model = "loaf_of_bread"
        self.scale = 0.2
        #self.create()

        # this is a dividable object, so define a piece
        self.piece = bread
        self.density =1000
        IsisObject.__init__(self)
        
        
        