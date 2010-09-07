from odeWorldManager import *

"""
Generic dynamic pickable object.
"""
class pickableObject(dynamicObject):
    def __init__(self, name, weight=0.5):
        
        self.icon = None
        
        """
        Weight will be the weight of the body.
        """
        self.weight = weight
        
        """
        Data for automatic geom, body and model setup.
        """
        self.friction = 10.1
        self.shape = "box"
        
        """
        This way we know what to do with the object when it's picked up.
        more in the selection callback
        """
        self.pickableType = "carry"
        
        """
        The character holding this item.
        """
        self.owner = None
        
        self.friction = 10.1
    
    """
    Automated geom, body and model setup. See map.py to see the usage of
    this method.
    """
    def setupGeomAndPhysics(self, physics, pos, quat):
        """
        Notice that I initiate this as a dynamic object here and not in the local __init__
        """
        dynamicObject.__init__(self, physics)
        
        self.surfaceFriction = self.friction
        
        """
        Load the model from the variable set in init.
        """
        self.setNodePath(self.activeModel, render)
        
        """
        Automatically create the geom shape.
        Only box and sphere because only these are currenly supported with set*
        methods in dynamicObject. And only those are supported by CCD.
        """
        if self.shape == "box":
            self.setBoxGeom(self.geomSize)
            self.setBoxBody(self.weight, self.geomSize)
        elif self.shape == "sphere":
            self.setSphereGeom(self.geomSize)
            self.setSphereBody(self.weight, self.geomSize)
        
        """
        Set bitmasks
        """
        self.setCatColBits("pickable")
        
        self.setPos(pos)
        self.setQuat(quat)
        
        self.physics.addObject(self)
    
    """
    While the Player initiates picking up, it's actually the pickable that
    picks itself up into the Player's inventory. This is a more flexible way.
    
    Note that this method was previously called "pickUp", but with the current
    version it's name must be selectionCallback (unified between all objects).
    """
    def selectionCallback(self, character, direction):
        result = character.pickUpItem(self)
        if not result:
            return False
            
        self.owner = character
        
        self.body.setLinearVel(0, 0, 0)
        self.body.setAngularVel(0, 0, 0)
        
        if self.pickableType == "carry":
            """
            So that the object doesn't block our view.
            """
            self.activeModel.setAlphaScale(0.5)
            self.activeModel.setTransparency(TransparencyAttrib.MAlpha)
            
        elif self.pickableType == "pocket":
            """
            Disable and hide, as it's usually done in games.
            """
            self.disablePhysics()
            self.activeModel.detachNode()
        
        #messenger.send("update_hud", [self.icon])
        
        return True
    
    def disablePhysics(self):
        self.body.disable()
        self.geom.disable()
        
    def resetPhysics(self):
        self.geom.enable()
        self.body.enable()
    
    """
    Use the object when it's being held by the Player. This is usually what gets called
    when the Player presses "fire". For guns you would put shooting here.
    """
    def useHeld(self):
        if not self.map.worldManager.collideSelected(self.geom):
            self.throw()
    
    def useHeldStop(self):
        return
    
    """
    Just like the pickables do the actual work of picking themselves up,
    they also drop themselves...
    """
    def drop(self):
        self.resetPhysics()
        self.nodePath.reparentTo(render)
        self.nodePath.setAlphaScale(1.0)
        
        self.body.setGravityMode(1)
        
        self.owner = None
        
        messenger.send("clear_hud")
    
    """
    ...and throw themselves when the Player asks them to.
    
    I also make sure they get their gravity back.
    """
    def throw(self, force=(10**3)):
        self.owner.throwHeld(force)
        self.body.setGravityMode(1)
        
    def destroy(self, task=None):
        if self.owner:
            self.owner.heldItem = None
        dynamicObject.destroy(self)
        

"""
A generic pickable box.
"""
class pickableBox(pickableObject):
    def __init__(self):
        pickableObject.__init__(self, "box", 0.5)
        self.geomSize = (1.0, 1.0, 1.0)
        self.friction = 1.0

"""
A generic pickable ball.
"""
class pickableBall(pickableObject):
    def __init__(self):
        pickableObject.__init__(self, "ball", 0.5)
        self.modelPath = "./graphics/models/ball.egg"
        self.shape = "sphere"
        self.geomSize = 0.25
        self.friction = 3.0
