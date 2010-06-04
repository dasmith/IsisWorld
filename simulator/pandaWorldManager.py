from pandac.PandaModules import *

# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)



class PhysicsCharacterController(object):
    
    
    def __init__(self, worldManager):

	# attach collision node
	self.geom = worldManager.addActorPhysics(self)
        if False:
	    #Collision handler for adding objects and the like
	    self.pTrav = CollisionTraverser("Picker Traverser")
	    self.pQueue = CollisionHandlerQueue()
	    base.cPush.addInPattern('%fn')
	    self.player = NodePath(ActorNode("player"))
	    self.player.reparentTo(render)

	    #Picker collision
	    pickerNode = CollisionNode('mouseRay')
	    pickerNP = self.fov.attachNewNode(pickerNode)
	    pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
	    pickerNode.setIntoCollideMask(BitMask32().allOff())
	    self.pickerRay = CollisionRay()
	    pickerNode.addSolid(self.pickerRay)
	    self.pTrav.addCollider(pickerNP, self.pQueue)

	    # Floor collision
	    self.playerGroundRay = CollisionRay()     # Create the ray
	    self.playerGroundRay.setOrigin(0,0,10)    # Set its origin
	    self.playerGroundRay.setDirection(0,0,-1) # And its direction
	    #self.ballGroundCol = CollisionNode('floorRay') # Create and name the node
	    #self.ballGroundCol.addSolid(self.playerGroundRay) # Add the ray
	    #self.ballGroundCol.setFromCollideMask(BitMask32.bit(1)) # Set its bitmasks
	    #self.ballGroundCol.setIntoCollideMask(BitMask32.allOff())
	    #self.ballGroundColNp = self.ralphFoot.attachNewNode(self.ballGroundCol)

	    #Player Collision Sphere
	    self.cNode = CollisionNode("PlayerCollision")

	    #To make the person tall, but not wide we use three collisionspheres
	    self.cNode.addSolid(CollisionSphere(0,0,-1,1))
	    self.cNode.addSolid(CollisionSphere(0,0,-3,1))
	    self.cNode.addSolid(CollisionSphere(0,0,-5,1))

	    self.cNodePath = self.player.attachNewNode(self.cNode)
	    self.cNodePath.node().setFromCollideMask(FLOORMASK|WALLMASK)
	    self.cNodePath.node().setIntoCollideMask(BitMask32.allOff())

	    base.cPush.addCollider(self.cNodePath, self.player)
	    base.cTrav.addCollider(self.cNodePath, base.cPush)

	    #Attach it to the global physics manager.
	    base.physicsMgr.attachPhysicalNode(self.player.node())

	    self.actor.reparentTo(self.player)
	    taskMgr.add(self.updateCharacter, "updateCharacter")

    def updateCharacter(self, task):
        """Big task that updates the character's visual and physical position every tick"""
        elapsed = globalClock.getDt() 

        if False:
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY()) 
            self.pTrav.traverse(render) 

            # Screen selection used to identify what the player is looking at 
            if self.pQueue.getNumEntries() > 0: 
                self.pQueue.sortEntries() 
                entry = self.pQueue.getEntry(0) 

                eName = entry.getIntoNodePath().getName() 
                ePos = entry.getSurfacePoint(render) 
                self.newpos = ePos 

                distVec = ePos - self.actor.getPos() 
                if distVec.length() < 12.0: 
                    self.objText['text'] = eName 
            self.vel = Vec3(x,y,0) 
        self.speed *= elapsed 
        self.player.setFluidPos(self.player, self.speed) 
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
        base.cTrav = CollisionTraverser('Collision Traverser') 
        base.cTrav.setRespectPrevTransform(True) 

        #Pusher Handler for walls 
        base.cPush = PhysicsCollisionHandler()
        # panda's physics system is attached to particle system
        base.enableParticles() 
       
        # init gravity
        self.gravityFN = ForceNode('gravity-force')
        self.gravityFNP = render.attachNewNode(self.gravityFN)
        self.gravityForce = LinearVectorForce(0,0,-9.81)
        self.gravityFN.addForce(self.gravityForce)
        
        base.physicsMgr.addLinearForce(self.gravityForce)

    def addActorPhysics(self,actor):
        geom = actor.actor.attachNewNode(CollisionNode('%s-collider'%actor.name))
        # set up geometry for collision node
        geom.node().addSolid(CollisionSphere(0,0,0,1))
        base.cTrav.addCollider(geom, base.cPush)
        return geom

    def addObjectInWord(nodePath,shape):
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
        self.groundGeom = CollisionPlane(Plane(Vec3(0,0,1), Point3(0,0,0)))
        self.groundCN = render.attachNewNode(CollisionNode('ground-collisionnode'))
        # TODO: attach new node as a sub-node of the ground image
        self.groundCN.node().addSolid(self.groundGeom)
        self.groundCN.show()


            #groundGeom = OdePlaneGeom(self.worldManager.space, Vec4(0, 0, 1, 0))
        #groundGeom.setCollideBits(BitMask32(0x00000021))
        #groundGeom.setCategoryBits(BitMask32(0x00000012))
        #groundData = OdeObject()
        #groundData.name = "ground"
        #groundData.surfaceFriction = 2.0
        #self.worldManager.setGeomData(groundGeom, groundData, None)
        #self.worldManager.world.setContactSurfaceLayer(.0001)

    def startPhysics(self):
        return True
        self.initCollision()