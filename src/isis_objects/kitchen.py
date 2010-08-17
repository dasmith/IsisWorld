from isisobject import *
from visual import *
from functional import *
from spatial import Room
from pandac.PandaModules import * # TODO: specialize this import
import random

class kitchen(IsisObject,IsisVisual,Room, NoPickup):

    def  __init__(self, physics):
        # store pointer to world manager
        self.physics = physics
        self.offsetVec = offsetVec=(0,0,0,0,0,0)
        self.scale=0.006
        self.density = 4000
        self.roomScale=35
        
        self.length =  random.randint(6, 9)*2
        self.width = random.randint(6, 9)*2
        self.height = random.randint(6, 9)
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
