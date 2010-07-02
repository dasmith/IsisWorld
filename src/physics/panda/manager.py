from direct.showbase import DirectObject
from pandac.PandaModules import * # TODO: specialize
# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(2)
AGENTMASK = BitMask32.bit(3)

class PhysicsWorldManager(DirectObject.DirectObject):
    
    def __init__(self):
        
        # enable the physics manager (and the particle manager...) and 
        # add base.updateManagers to the task manager in ShowBase. 
        # This causes base.physicsMgr.doPhysics(dt) to be called each frame 
        base.enableParticles() 
        # we don't actually care about particles, so disable them again. 
        base.particleMgrEnabled = 0
        
        
        gravityFN = ForceNode('gravity')
        gravityNP = render.attachNewNode(gravityFN)
        gravityForce = LinearVectorForce(0, 0, -9.81)
        gravityFN.addForce(gravityForce)
        base.physicsMgr.addLinearForce(gravityForce)
        
        self.cHandler = CollisionHandlerQueue()
        base.cTrav = CollisionTraverser( ) 
        base.cTrav.showCollisions( render )
        #base.physicsMgr.doPhysics(dt)

    def startPhysics(self):
        # everything is done in the __init__ method
        # for Panda's physics
        pass


class PhysicsCharacterController(object):
    
    def __init__(self, worldManager):
        # make sure parent node is off
        import random
        self.rootNode.setCollideMask(BitMask32.allOff())
        x = random.randint(0, 10)
        y = random.randint(0, 10)
        z = random.randint(0, 10)
        self.actor.setPos(x, y, z)
        self.avatarRadius = 0.8        
        offsetNodeOne = [x, 0 + y, 0.5 + z, 0.5]
        offsetNodeTwo = [x, 0 + y, 1.6 + z, 0.5]
        # collision tubes have not been written as good FROM collidemasks
        # to make the person tall, but not wide we use three collisionspheres
        centerHeight = 0.8
        self.avatarViscosity = 0
        self.cNode = CollisionNode('collisionNode')
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight, self.avatarRadius))
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight + 2 * self.avatarRadius, self.avatarRadius))
        self.cNode.setFromCollideMask(BitMask32.allOn())
        self.cNode.setIntoCollideMask(BitMask32.allOff() | AGENTMASK)
        self.cNode.setTag('agent', 'agent')
        self.cNodePath = self.actor.attachNewNode(self.cNode)
        self.cNodePath.show()
        self.priorParent, self.actorNodePath, self.acForce = worldManager.addActorPhysics(self)

def getOrientedBoundedBox(collobj):
    ''' get the oriented bounding box '''
    # save object's parent and transformation
    parent = collobj.getParent()
    trans = collobj.getTransform()
    # ode need everything in world's coordinate space,
    # so bring the object directly under render, but keep the transformation
    collobj.wrtParentTo(render)
    # get the tight bounds before any rotation
    collobj.sethpr(0, 0, 0)
    bounds = collobj.getTightBounds()
    # bring object to it's parent and restore it's transformation
    collobj.reparentTo(parent)
    collobj.settransForm(trans)
    # (max - min) bounds
    box = bounds[1] - bounds[0]
    return [box[0], box[1], box[2]]


def getCapsuleSize(collobj, radius=1):
    bounds = collobj.getTightBounds()
    # (max - min) bounds
    return [bounds[0][0], bounds[0][1], bounds[0][2], bounds[1][0], bounds[1][1], bounds[1][2], radius]
