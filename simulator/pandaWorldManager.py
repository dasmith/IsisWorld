
from pandac.PandaModules import *
# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(1)


class PhysicsCharacterController(object):
    
    def __init__(self, worldManager):
        # add velocity
        self.velocity = Vec3(0.0,0.0,0.0)
        self.geom = worldManager.addActorPhysics(self)
        taskMgr.add(self.updateCharacter, "updateCharacter-%s" % self.name)
        #self.geom = worldManager.addActorPhysics(self)
        # turn off mask on model
        self.actor.setCollideMask(BitMask32.allOff())
        # setup ground ray
        self.physicsGroundRay = CollisionRay()
        self.physicsGroundRay.setOrigin(0,0,10)
        self.physicsGroundRay.setDirection(0,0,-1)
        self.physicsGroundCol = CollisionNode('%s-collision-ground' % self.name)
        self.physicsGroundCol.addSolid(self.physicsGroundRay)
        self.physicsGroundCol.setFromCollideMask(FLOORMASK)
        self.physicsGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.physicsGroundHandler = CollisionHandlerQueue()
        self.physicsGroundColNP =  self.actor.attachNewNode(self.physicsGroundCol)
        base.cTrav.addCollider(self.physicsGroundColNP,self.physicsGroundHandler)

    def updateCharacter(self, task):
        """Big task that updates the character's visual and physical position every tick"""
        elapsed = globalClock.getDt() 
        avatar = self.geom.getChild(0).getChild(0)
        # check to see if he's falling
        if False: #self.physicsGroundHandler.getNumEntries() > 0:
            self.physicsGroundHandler.sortEntries()
            entry = self.physicsGroundHandler.getEntry(0)
            eName = entry.getIntoNodePath().getName()
            ePos = entry.getSurfacePoint(render)
            print "Colliding with ", eName
            #avatar.setPos(ePos)
        else:
            # he's falling!
            1 + 1
            #avatar.setZ(self.actor.getZ()-0.98)
        self.velocity *= elapsed
        self.actor.setFluidPos(avatar, self.velocity)
        return task.cont 

def getOrientedBoundingBox(collObj):
    ''' get the Oriented Bounding Box '''
    # save object's parent and transformation
    parent=collObj.getParent()
    trans=collObj.getTransform()
    # ODE need everything in world's coordinate space,
    # so bring the object directly under render, but keep the transformation
    collObj.wrtReparentTo(render)
    # get the tight bounds before any rotation
    collObj.setHpr(0,0,0)
    bounds=collObj.getTightBounds()
    # bring object to it's parent and restore it's transformation
    collObj.reparentTo(parent)
    collObj.setTransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
    return [box[0],box[1],box[2]]


class PhysicsWorldManager():
    
    def __init__(self):
        """Setup the collision pushers, handler, and traverser"""
        # cTrav is in charage to drive collisions
        base.cTrav = CollisionTraverser('Collision Traverser')
        # panda's physics system is attached to particle system
        base.enableParticles()
        # allows detection of fast moving objects
        #base.cTrav.setRespectPrevTransform(True)
        base.cPush = PhysicsCollisionHandler()
        #base.cEvent = CollisionHandlerEvent()

        # init gravity force
        self.gravityFN = ForceNode('gravity-force')
        self.gravityFNP = base.render.attachNewNode(self.gravityFN)
        # drag down in Z axis -9.81 units/second
        self.gravityForce = LinearVectorForce(0,0,-9.81)

        # attach gravity to global physics manager, which
        # is defined automatically by base.enableParticles()
        base.physicsMgr.addLinearForce(self.gravityForce)

        #base.cPush.addInPattern("%fn-into-everything")
        #base.cEvent.addAgainPattern("%fn-again-%in")

    def addActorPhysics(self,actor):
        # Whenever we want to inter-act with anything to do with collisions/physics,
        # we want to use the actor node path
        charAN = ActorNode("%s-actorNode" % actor.name)
        charNP = NodePath(actor.actor)#NodePath(PandaNode("%s-pandaNode" % actor.name))
        charANP = charNP.attachNewNode(charAN)


        #actor.actor.reparentTo(charANP)

        cNode = charANP.attachNewNode(CollisionNode('%s-collider'%actor.name))
        #To make the person tall, but not wide we use three collisionspheres
        cNode.node().addSolid(CollisionSphere(0,0,1,1))
        # THIS KILLS IT base.physicsMgr.attachPhysicalNode(charAN)
        #cNode.node().addSolid(CollisionSphere(0,0,-3,1))
        #cNode.node().addSolid(CollisionSphere(0,0,-5,1))
        #cNode.node().setFromCollideMask(FLOORMASK|WALLMASK)
        cNode.node().setFromCollideMask(BitMask32.allOn())
        cNode.node().setIntoCollideMask(BitMask32.allOff())
        cNode.show()
        # attach collision node with actor node to it
        base.cPush.addCollider(cNode, charANP)
        # add collider to global traverser
        base.cTrav.addCollider(cNode, base.cPush)

        charNP.reparentTo(base.render)
        #actor.actor.reparentTo(player)
        #Attach it to the global physics manager.
        #actor.actor.reparentTo(player)
        #jtaskMgr.add(self.updateCharacter, "updateCharacter")
        # set up geometry for collision node
        #geom.node().addSolid(CollisionSphere(0,0,0,1))
        #base.cTrav.addCollider(geom, base.cPush)
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

        #groundNP.node().setIntoCollideMask(FLOORMASK)

    def startPhysics(self):
        return True
        self.initCollision()