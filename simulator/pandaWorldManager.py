
from pandac.PandaModules import *
# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(2)
AGENTMASK = BitMask32.bit(3)


class PhysicsCharacterController(object):
    
    def __init__(self, worldManager):
        # add velocity
        self.velocity = Vec3(0.0,0.0,0.0)
        self.actor.setCollideMask(BitMask32.allOff())
        self.geom = worldManager.addActorPhysics(self)
        taskMgr.add(self.updateCharacter, "updateCharacter-%s" % self.name)
        #self.geom = worldManager.addActorPhysics(self)
        # turn off mask on model
        # setup ground ray
        self.pickerRay = CollisionRay()
        #self.pickerRay.setDirection(1,0,0)
        self.pickerCol = CollisionNode('%s-collision-ground' % self.name)
        self.pickerColNP =  self.player_eye.attachNewNode(self.pickerCol)
        self.pickerCol.addSolid(self.pickerRay)
        self.pickerCol.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(self.pickerColNP,self.pickerHandler)

    def updateCharacter(self, task):
        """Big task that updates the character's visual and physical position every tick"""
        elapsed = globalClock.getDt() 
        avatar = self.geom#.getChild(0)#.getChild(0)
        # check to see if he's falling
        if self.pickerHandler.getNumEntries() > 0:
            self.pickerHandler.sortEntries()
            entry = self.pickerHandler.getEntry(0)
            eName = entry.getIntoNodePath().getName()
            ePos = entry.getSurfacePoint(render)
            print "Colliding with ", eName
            #avatar.setPos(ePos)
        self.velocity *= elapsed
        avatar.setFluidPos(avatar, self.velocity)
        return task.cont 

def getorientedboundingbox(collobj):
    ''' get the oriented bounding box '''
    # save object's parent and transformation
    parent=collobj.getparent()
    trans=collobj.gettransform()
    # ode need everything in world's coordinate space,
    # so bring the object directly under render, but keep the transformation
    collobj.wrtreparentto(render)
    # get the tight bounds before any rotation
    collobj.sethpr(0,0,0)
    bounds=collobj.gettightbounds()
    # bring object to it's parent and restore it's transformation
    collobj.reparentto(parent)
    collobj.settransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
    return [box[0],box[1],box[2]]


def getCapsuleSize(collobj,radius=1):
    bounds=collobj.getTightBounds()
    # (max - min) bounds
    return [bounds[0][0],bounds[0][1],bounds[0][2],bounds[1][0],bounds[1][1],bounds[1][2],radius]

class PhysicsWorldManager():
    
    def __init__(self):
        """Setup the collision pushers, handler, and traverser"""
        # cTrav is in charage to drive collisions
        base.cTrav = CollisionTraverser('Collision Traverser')
        # panda's physics system is attached to particle system
        base.enableParticles()
        # allows detection of fast moving objects
        base.cTrav.setRespectPrevTransform(True)
        base.cPush = PhysicsCollisionHandler()
        #base.cEvent = CollisionHandlerEvent()

        # init gravity force
        self.gravityFN = ForceNode('gravity-force')
        self.gravityFNP = base.render.attachNewNode(self.gravityFN)
        # drag down in Z axis -9.81 units/second
        self.gravityForce = LinearVectorForce(0,0,-9.81)
        self.gravityFN.addForce(self.gravityForce)
        # attach gravity to global physics manager, which
        # is defined automatically by base.enableParticles()
        base.physicsMgr.addLinearForce(self.gravityForce)

        #base.cPush.addInPattern("%fn-into-everything")
        #base.cEvent.addAgainPattern("%fn-again-%in")

    def addActorPhysics(self,actor):
        # ActorNode tracks physical interactions and applies
        # them to a model.  It keeps track of the elapsed times
        # in framerates
        import random
        x= random.randint(0,10)
        y= random.randint(0,10)
        z= random.randint(0,10)
        #actor.actor.getPos()
        actor.actor.setPos(x,y,z)
        offsetNodeOne = [x,0+y,0.5+z,0.5]
        offsetNodeTwo = [x,0+y,1.6+z,0.5]
        charAN = ActorNode("%s-physicsActorNode" % actor.name)
        charAN.getPhysicsObject().setMass(100)
        charNP = NodePath(PandaNode("%s-physicsNode" % actor.name))
        charANP = charNP.attachNewNode(charAN)
        actor.actor.reparentTo(charANP)
        cNode = charANP.attachNewNode(CollisionNode('%s-collider'%actor.name))
        # collision tubes have not been written as good FROM collidemasks
        #cNode.node().addSolid(CollisionTube(*getCapsuleSize(actor.actor,2)))
        #To make the person tall, but not wide we use three collisionspheres
        cNode.node().addSolid(CollisionSphere(*offsetNodeOne))
        cNode.node().addSolid(CollisionSphere(*offsetNodeTwo))
        cNode.node().setIntoCollideMask(BitMask32.allOff())
        #cNode.node().setFromCollideMask(FLOORMASK|WALLMASK)
        cNode.node().setFromCollideMask(BitMask32.allOn())
        cNode.show()
        # let ralph fall, so he doesn' 
        charNP.setZ(10)
        base.physicsMgr.attachPhysicalNode(charAN)
        # attach collision node with actor node to it
        base.cPush.addCollider(cNode, charANP)
        # add collider to global traverser
        base.cTrav.addCollider(cNode, base.cPush)
        charNP.reparentTo(base.render)
        return charNP

    def addObjectInWorld(nodePath,shape):
        if self.disable: return
        collider = nodePath.attachNewNode(CollisionNode(nodePath.name+"-collider"))
        boundingBox=getOrientedBoundingBox(collObj)
        if shape=='sphere':
            radius=.5*max(*boundingBox)
            geom = OdeSphereGeom(space, radius)
            #self.geom.setPosition(obj.getPos(render))
            #self.geom.setQuaternion(obj.getQuat(render))
            return geom

    def setupGround(self,groundNP):

        # Ground collision: represented as an infinite plane
        # any object below the plane, no matter how far, is
        # considered to be intersecting the plane.
        #
        # Constructed with Panda3D plane object, one way to
        # do this is with a point and a normal
        cp = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        planeNP = base.render.attachNewNode(CollisionNode('planecnode'))
        planeNP.node().addSolid(cp)
        planeNP.show()

        groundNP.node().setIntoCollideMask(FLOORMASK)

    def startPhysics(self):
        return True
        self.initCollision()