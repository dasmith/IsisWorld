from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject
from layout_manager import SlotLayout

from direct.interval.IntervalGlobal import *
from random import *

PHYSICS = None
def setPhysics(physics):
    global PHYSICS
    PHYSICS = physics


class table(IsisObject,IsisVisual,Container,Surface,NoPickup):

    def  __init__(self):
        # store pointer to world manager
        self.physics =PHYSICS
        self.offsetVec = offsetVec=(0,0,0,0,0,0)
        self.model = "table/table"
        self.scale=0.006
        self.density = 4000

        IsisObject.__init__(self)

        self.setH(180)


class fridge(IsisObject, IsisVisual, Container, NoPickup):
    
    def  __init__(self):
        # store pointer to world manager
        self.physics =PHYSICS
        self.model={'default':"Fridge/Fridge"}
        self.scale=0.17
        self.density = 4000
        self.registerState("openState", "closed")

        IsisObject.__init__(self)

        self.in_layout = SlotLayout([(0, 0, .5), (0, 0, 1),(0, 0, 1.5)])

    def afterSetup(self):

        fd = self.activeModel.find("**/freezerDoor*")
        fd.setPos(-.56, .6, 1.65)
        self.door = self.activeModel.find("**/fridgeDoor*")
        self.door.setPos(-0.56, .6, .72)
        self.door.setCollideMask(BitMask32.allOff())
        self.setH(0)

    def action__open(self, agent, directobj):
        print "Select method called"
        if self.retrieveState("openState") == "closed":
            Sequence(
                Func(self.registerState, "openState", "opening"),
                LerpPosHprInterval(self.door, 0.5, Vec3(.45, 2.4, .72), Vec3(-90, 0, 0)),
                Func(self.registerState, "openState", "opened")
            ).start()
        elif self.retrieveState("openState") == "opened":
            Sequence(
                Func(self.registerState, "openState", "closing"),
                LerpPosHprInterval(self.door, 0.5, Vec3(-.56, .6, .72), Vec3(0, 0, 0)),
                Func(self.registerState, "openState", "closed")
            ).start()


class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def  __init__(self): 
        # store pointer to world manager
        self.physics =PHYSICS
        self.offsetVec = (0,0,0.0,0,0,0)
        self.pickupVec = (0,.15,0,0,75,0)
        self.model="knife"
        self.scale=0.01
        self.density = 25
        IsisObject.__init__(self)

class toaster(IsisObject, IsisVisual, Container, Cooker):
    
    def __init__(self):
        self.physics =PHYSICS
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

    def  __init__(self):
        # store pointer to world manager
        self.physics =PHYSICS

        self.offsetVec = (0,0,-.1,0,-120,-20)
        self.pickupVec=(-.125,.225,0,0,-125,0)
        self.model={"default":"slice_of_bread", "toast":"piece_of_toast"}
        self.scale = 0.5
        
        self.density = 200
        
        self.cookableCookedModel = "toast"
        IsisObject.__init__(self)

class loaf( IsisObject, IsisVisual, IsisSpatial, Dividable):

    def  __init__(self): 
        # store pointer to world manager
        self.physics =PHYSICS
        self.offsetVec = (.00144,0,0.0,0,0,0)
        
        self.model = "loaf_of_bread"
        self.scale = 0.2
        #self.create()

        # this is a dividable object, so define a piece
        self.piece = bread
        self.density =1000
        IsisObject.__init__(self)


class kitchen(IsisObject,IsisVisual,Room, NoPickup):

    def  __init__(self):
        # store pointer to world manager
        self.physics =PHYSICS
        self.offsetVec = offsetVec=(0,0,0,0,0,0)
        self.scale=0.006
        self.density = 4000
        self.roomScale=35
        
        self.length =  randint(6, 9)*2
        self.width = randint(6, 9)*2
        self.height = randint(6, 9)
        self.activeModel = NodePath('kitchen')
        # don't allow model to ever be changed. since model is a pointer to a procedurally generated visual model, it doesn't behave like an egg file
        self.staticModel = True
        IsisObject.__init__(self)

    def setup(self):
        """ This actual model gets generated after the kitchen is initialized
        to allow for configurations to override the defaults"""
        
        
        self.activeModel.setCollideMask(BitMask32.allOff())
        
        CM=CardMaker('')

        hw = self.width/2
        hl = self.length/2
        # walls
        CM.setFrame(-hw,hw,0,self.height)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(0, hl, 0, 0, 0, 0)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(0, -hl, 0, 180, 0, 0)
        CM.setFrame(-hl,hl,0,self.height)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(hw, 0, 0, -90, 0, 0)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(-hw, 0, 0, 90, 0, 0) 
        self.activeModel.setCollideMask(WALLMASK)
        floorTex=loader.loadTexture("media/maps/grid.rgb")#os.path.join(self.rootDirectory,"media","maps","grid.rgb"))
        floorTex.setMinfilter(Texture.FTLinearMipmapLinear) 
        floorTex.setMagfilter(Texture.FTLinearMipmapLinear) 
        wallTex=loader.loadTexture("media/textures/concrete.jpg")#os.path.join(self.rootDirectory,"media","textures","concrete.jpg"))
        wallTex.setMinfilter(Texture.FTLinearMipmapLinear) 
        for wall in self.activeModel.getChildrenAsList(): 
           wall.setTexture(wallTex) 
           wall.setTexScale(TextureStage.getDefault(),0.5,self.height*self.roomScale*10)
        CM.setFrame(-hw,hw,-hl,hl) 
        floor=self.activeModel.attachNewNode(CM.generate()) 
        floor.setTexture(floorTex)
        floor.setTexScale(TextureStage.getDefault(),10,10,10)
        floor.setP(-90)
        floor.setZ(0.01)
        self.activeModel.setTransparency(TransparencyAttrib.MAlpha) 
        self.activeModel.setTwoSided(1) 
        self.activeModel.flattenLight()
