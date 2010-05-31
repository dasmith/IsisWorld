from pandac.PandaModules import *

# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)



class PhysicsCharacterController(object):
    
    
    def __init__(self, base ):
  
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
        taskMgr.add(self.updatePlayer, "updatePlayer")

    def updatePlayer(self, task): 
        """Big task that updates the players position every tick""" 
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


class PhysicsWorldManager():
    
    
    
    def __init__(self):
        """Setup the collision pushers and traverser""" 
        #Generic traverser 
        base.cTrav = CollisionTraverser('Collision Traverser') 
        base.cTrav.setRespectPrevTransform(True) 

        #Pusher Handler for walls 
        base.cPush = PhysicsCollisionHandler() 

        base.enableParticles() 
       
        # init gravity
        self.gravityFN = ForceNode('gravity-force')
        self.gravityFNP = render.attachNewNode(self.gravityFN)
        self.gravityForce = LinearVectorForce(0,0,-9.81)
        self.gravityFN.addForce(self.gravityForce)
        
        base.physicsMgr.addLinearForce(self.gravityForce)
        
    def addObjectInWord(nodePath):
        collider = nodePath.attachNewNode(CollisionNode(nodePath.name+"-collider"))
        
        

    def startPhysics(self):
        return True
        self.initCollision()