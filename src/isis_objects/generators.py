
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject
from layout_manager import SlotLayout

from direct.interval.IntervalGlobal import *

@IsisObject
class table(NodePath,IsisVisual,Container,Surface,NoPickup):

    def __init__(self):
        self.offsetVec = offsetVec=(0,0,0,0,0,0)
        
        self.model = "table/table"
        self.scale=0.006
        #self.setH(180)

        #self.create()
        
        self.density = 4000

@IsisObject
class fridge(NodePath, IsisVisual, Container, NoPickup):
    
    def __init__(self,name):

        # construct parent NodePath class
        NodePath.__init__(self, name)



        self.model={'default':"Fridge/Fridge"}
        #self.setH(-90)
        self.scale=0.17
        
        self.density = 4000
        
        self.in_layout = SlotLayout([(0, 0, .5), (0, 0, 1),(0, 0, 1.5)])

        self.state = "closed"

    def setup(self):
        fd = self.activeModel.find("**/freezerDoor*")
        fd.setPos(-.56, .6, 1.65)
        self.door = self.activeModel.find("**/fridgeDoor*")
        self.door.setPos(-0.56, .6, .72)


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

@IsisObject
class knife(NodePath, IsisVisual, IsisSpatial, Sharp):

    def __init__(self,name):

        # construct parent NodePath class
        NodePath.__init__(self, name)
        self.pickupVec = (0,.15,0,0,75,0)
        self.model="knife"
        self.scale=0.01
        self.density = 25

@IsisObject
class toaster(NodePath, IsisVisual, Container, Cooker):
    
    def __init__(self,name):

        # construct parent NodePath class
        NodePath.__init__(self, name)
        ######### Base Variables ##########
         # visual offset for the model's position and rotation
        self.offsetVec = (.5,.16,.19,-8,0,0)
        
        ######## Visual Parameters ###############
        # store a model, either as a string or a dictionary
        self.model = "toaster"
        self.scale = 0.7
        self.create()

        ######## Spatial Parameters ##############
        self.density = 100
        
                #Container.setup(self)
        self.on_layout = SlotLayout([(.3, .1, .2), (.3, -.1, .2)])

        ######## Functional Parameters ############
        self.cook_in = True
        self.cook_on = False
        
        self.registerState("containsToast", [0,1,2])

@IsisObject
class bread(NodePath, IsisVisual, Container, Cookable):

    def __init__(self,name):

        # construct parent NodePath class
        NodePath.__init__(self, name)
        self.offsetVec = (0,0,-.1,0,-120,-20)
        self.pickupVec=(-.125,.225,0,0,-125,0)
        self.model={"default":"slice_of_bread", "toast":"piece_of_toast"}
        self.scale = 0.5
        
        self.density = 200
        
        self.cookableCookedModel = "toast"

@IsisObject
class loaf( NodePath, IsisVisual, IsisSpatial, Dividable):

    def __init__(self,name):

        # construct parent NodePath class
        NodePath.__init__(self, name)
        self.offsetVec = (.00144,0,0,0,0,0)
        
        self.model = "loaf_of_bread"
        self.scale = 0.2
        #self.create()

        self.density =1000
        
        