""" 
Defining a new object.

1: Begin with this template.

class object_name(IsisObject,IsisVisual,IsisSpatial,IsisFunctional):

    def __init__(self, **kwargs):
        
        self.model = "name_of_egg_file"
        
        # either 
        self.generate_scale_between()
        # OR a fixed scale
        self.scale = 1.0
        
        # optionally, default x,y,z,h,p,r offsets
        self.offset_vector = (0,0,0,180,0,0)  # rotates 180 degrees along x-axis
        
        # REQUIRED last line of the initialization method
        IsisObject.__init__(self, **kwargs)
        
    def after_setup():
        # optional method to call after setup

"""


from random import *

from pandac.PandaModules import Vec3
from direct.interval.IntervalGlobal import *

from visual import *
from functional import *
from spatial_ode import *
from isis_object import IsisObject
from layout_manager import SlotLayout
from ..isis_agents.isis_agent import IsisAgent
from ..physics.ode.pickables import *
from ..physics.ode.odeWorldManager import *

class table(IsisObject,IsisVisual,SpatialStaticBox,Surface,IsisFunctional):

    def __init__(self, **kwargs):

        self.model = "table/table"
        self.generate_scale_between(6,9)
        
        self.offset_vector = (0,0,0,180,0,0)

        IsisObject.__init__(self, **kwargs)

class fridge(IsisObject, IsisVisual, SpatialStaticBox, Container, FunctionalDoor):
    
    def  __init__(self, **kwargs):
        

        self.model={'default':"Fridge/Fridge"}
        self.generate_scale_between(.16,.20)
        self.density = 4000
        
        self.in_layout = SlotLayout([(0, 0, .5), (0, 0, 1),(0, 0, 1.5)])
        IsisObject.__init__(self, **kwargs)

    def after_setup(self):
        # add the door
        fd = self.activeModel.find("**/freezerDoor*")
        fd.setPos(-.56, .6, 1.65)
        self.door = self.activeModel.find("**/fridgeDoor*")
        self.door.setPos(-0.56, .6, .72)
        #self.door.setCollideMask(BitMask32.allOff())
        self.setH(0)
        

    def action__open(self, agent, indrect_object):
        
        if not self.get_attribute_value('is_open'):
            Sequence(
                LerpPosHprInterval(self.door, 0.5, Vec3(.45, 2.4, .72), Vec3(-90, 0, 0)),
                Func(self.set_attribute, 'is_open', True)
            ).start()
        else:
            Sequence(
                LerpPosHprInterval(self.door, 0.5, Vec3(-.56, .6, .72), Vec3(0, 0, 0)),
                Func(self.set_attribute, 'is_open', False)
            ).start()


class knife(IsisObject, IsisVisual, SpatialPickableBox, Sharp):

    def  __init__(self, **kwargs):
        self.offset_vector = (0,0,0.0,0,0,0)
        self.pickup_vector = (0,.15,0,0,75,0)
        self.model="knife"
        self.scale=0.01
        self.density = 25
        IsisObject.__init__(self, **kwargs)

class toaster(IsisObject, IsisVisual, SpatialPickableBox, Cooker):
    
    def __init__(self, **kwargs):
        ######### Base Variables ##########
         # visual offset for the model's position and rotation
        self.offset_vector = (.5,.16,.19,-8,0,0)
        
        ######## Visual Parameters ###############
        # store a model, either as a string or a dictionary
        self.model = "toaster"
        self.scale = 0.7
        ######## Spatial Parameters ##############
        self.density = 1000
        self.on_layout = SlotLayout([(.3, .1, .2), (.3, -.1, .2)])

        ######## Functional Parameters ############
        self.cook_in = True
        self.cook_on = False
        
        #self.registerState("containsToast", [0,1,2])
        IsisObject.__init__(self, **kwargs)

class bread(IsisObject, IsisVisual, SpatialPickableBox, Cookable):

    def __init__(self, **kwargs):
        self.offset_vector = (0,0,-.1,0,-120,-20)
        self.pickup_vector=(-.125,.225,0,0,-125,0)
        self.model={"default":"slice_of_bread", "toast":"piece_of_toast"}
        self.scale = 0.5
        
        self.density = 200
        
        self.cookableCookedModel = "toast"
        IsisObject.__init__(self, **kwargs)

class butter(IsisObject, IsisVisual, SpatialPickableBox, IsisFunctional ):

    def  __init__(self, **kwargs):
        self.offset_vector = (-0.8,0.3,0.0,90,0,180)
        self.pickup_vector=(-.125,.225,0,0,-125,0)
        self.model={"default":"butter"}
        self.scale = 0.05
        
        self.density = 200
        
        IsisObject.__init__(self, **kwargs)

class loaf( IsisObject, IsisVisual, SpatialPickableBox, Dividable):

    def __init__(self, **kwargs):
        self.offset_vector = (.00144,0,0.0,0,0,0)
        
        self.model = "loaf_of_bread"
        self.scale = 0.2
        #self.create()

        # this is a dividable object, so define a piece
        self.piece = bread
        self.density =1000
        IsisObject.__init__(self, **kwargs)


class kitchen(IsisObject,IsisVisual,SpatialRoom,IsisFunctional):

    def  __init__(self, **kwargs):
        self.offset_vector = offset_vector=(0,0,0,0,0,0)
        self.density = 4000
        self.roomScale=35
        self.length =  randint(6, 9)*2
        self.width = randint(6, 9)*2
        self.height = randint(6, 9)
        self.activeModel = NodePath('kitchen')
        # don't allow model to ever be changed. since model is a pointer to a procedurally generated visual model, it doesn't behave like an egg file
        self.staticModel = True
        IsisObject.__init__(self, **kwargs)

    def setup(self):
        """ This actual model gets generated after the kitchen is initialized
        to allow for configurations to override the defaults"""
        
        CM=CardMaker('kitchenNode')

        hw = self.width/2
        hl = self.length/2
        print "KITCHEN WIDTH/LENTH", hw, hl
        # walls
        CM.setFrame(-hw,hw,0,self.height)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(0, hl, 0, 0, 0, 0)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(0, -hl, 0, 180, 0, 0)
        CM.setFrame(-hl,hl,0,self.height)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(hw, 0, 0, -90, 0, 0)
        self.activeModel.attachNewNode(CM.generate()).setPosHpr(-hw, 0, 0, 90, 0, 0) 
        self.activeModel.setCollideMask(WALLMASK)
        floorTex=loader.loadTexture("media/maps/grid.rgb")
        floorTex.setMinfilter(Texture.FTLinearMipmapLinear) 
        floorTex.setMagfilter(Texture.FTLinearMipmapLinear) 
        wallTex=loader.loadTexture("media/textures/concrete.jpg")
        wallTex.setMinfilter(Texture.FTLinearMipmapLinear) 
        for wall in self.activeModel.getChildren(): 
           #wall.setTexture(wallTex)
           wall.setColorScale(0.9,0.9,0.5, 1.0)
           #wall.setTexScale(TextureStage.getDefault(),0.5,self.height*self.roomScale*100)
        CM.setFrame(-hw,hw,-hl,hl) 
        floor=self.activeModel.attachNewNode(CM.generate()) 
        floor.setTexture(floorTex)
        floor.setTexScale(TextureStage.getDefault(),8,8,8)
        floor.setColorScale(1.0,1.0,1.0, 1.0)
        floor.setP(-90)
        floor.setZ(0.01)
        self.activeModel.setTransparency(TransparencyAttrib.MAlpha) 
        self.activeModel.setTwoSided(1) 
        self.activeModel.flattenLight()

