from direct.showbase import DirectObject
from pandac.PandaModules import * # TODO: specialize
# initialize collision mask constants  
FLOORMASK = BitMask32.bit(1)      
WALLMASK = BitMask32.bit(2)
PICKMASK = BitMask32.bit(3)
AGENTMASK = BitMask32.bit(4)
OBJMASK= BitMask32.bit(5)

def getOrientedBoundedBox(collObj):
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
    offset=collObj.getBounds().getCenter()-collObj.getPos()
    # bring object to it's parent and restore it's transformation
    collObj.reparentTo(parent)
    collObj.setTransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
#        print bounds[0], bounds[1]
    return [box[0],box[1],box[2]], [offset[0],offset[1],offset[2]]
    
    
class PhysicsWorldManager(DirectObject.DirectObject):
    
    def __init__(self):
        """ Initialize the 3 Collision Handlers and the base Traverser, which looks
        through the entire node path. 
        
        Future optimization: traversers that only look at certain branches of the render tree.
        """
        self._GlobalClock=ClockObject.getGlobalClock() 
        self._FrameTime=self._GlobalClock.getFrameTime() 
        self._GlobalClock.setRealTime(self._FrameTime) 
        
        # run the physical simulator 1.0/X = X times per sec
        self.stepSize = 1.0/50.0
        self.deltaTimeAccumulator = 0.0
        
        # keep track of all agents
        self.agents = []
     
        if False:
            base.enableParticles()
            self.cHandler = PhysicsCollisionHandler()
            gravityFN = ForceNode('gravity')
            gravityNP = render.attachNewNode(gravityFN)
            gravityForce = LinearVectorForce(0, 0, -9.81)
            gravityFN.addForce(gravityForce)
            base.physicsMgr.addLinearForce(gravityForce)  

        # Initialize the collision traverser.
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True)
        #base.cTrav.showCollisions( render )

        # initialize 3 handlers: wall, gravity, and other events
        
        # the CollisionHandlerPusher is good for keeping items from going through walls
        self.cWall = CollisionHandlerPusher()
        
        # this tracks the velocity of moving objects, whereas CollisionHandlerFloor doesnt
        self.cFloor = CollisionHandlerGravity()
        # gravity should be -9.81m/s, but that doesn't quite work
        self.cFloor.setGravity(9.81*10)
        self.cFloor.setOffset(.9)
        self.cFloor.setMaxVelocity(100)
        #self.cFloor.setLegacyMode(True)
        self.cFloor.addInPattern('into')

        # Initialize the handler.
        base.cEvent = CollisionHandlerEvent()
        base.cEvent.addInPattern('%fn-into-%in')
        base.cEvent.addOutPattern('%fn-outof-%in')
       
        # initialize listeners
        base.accept('into', self._floor)
        base.accept('object-into-object', self._objCollisionHandlerIn)
        base.accept('object-outof-object', self._objCollisionHandlerOut)
        base.accept('agent-into-object', self._agentCollisionHandlerIn)
        base.accept('agent-into-agent', self._agentsCollisionIn)

        # start it up 
        self.paused = False 
        self._startPhysics()
    
    def _floor(self, entry):
        cFrom = entry.getFromNodePath().getParent()
        cInto = entry.getIntoNodePath().getParent()
        print "Floor Collision: %s, %s" % (cFrom, cInto)
    
    def _objCollisionHandlerIn(self, entry):
        cFrom = entry.getFromNodePath().getParent()
        cInto = entry.getIntoNodePath().getParent()
        print "Object In Collision: %s, %s" % (cFrom, cInto)

    def _objCollisionHandlerOut(self, entry):
        cFrom = entry.getFromNodePath().getParent()
        cInto = entry.getIntoNodePath().getParent()
        print "Object Out Collision: %s, %s" % (cFrom, cInto)

    def _agentCollisionHandlerIn(self, entry):
        agent = entry.getFromNodePath().getParent()
        cInto = entry.getIntoNodePath().getParent()
        print "Agent In Collision: %s, %s" % (agent, cInto)

    def _agentsCollisionIn(self, entry):
        agentFrom = entry.getFromNodePath().getParent()
        agentInto = entry.getIntoNodePath().getParent()
        print "Agents collided : %s, %s" % (agentFrom, agentInto) 

    
    def addAgent(self,agent):
        self.agents.append(agent)

    def setupGround(self):
        return # do nothing 
        # First we create a floor collision plane.
        # Create a collision plane solid.
        collPlane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        floorCollisionNP = base.render.attachNewNode(CollisionNode('collisionNode'))
        floorCollisionNP.node().addSolid(collPlane) 
        floorCollisionNP.node().setIntoCollideMask(FLOOR_MASK)
        
    def stepSimulation(self,stepTime=1):
        if self.paused:
            self.togglePaused(stepTime)
        else:
            print "Error, cannot step while simulator is running"
        
    def togglePaused(self,stepTime=None):
        if self.paused: 
            #self._GlobalClock.setMode(ClockObject.MNormal) 
            #base.enableParticles()
            #base.particleMgrEnabled = 0 
            print "[IsisWorld] Resuming Simulator"
            self._startPhysics(stepTime)
        else:
            self._stopPhysics()
            #self._GlobalClock.setMode(ClockObject.MSlave)
        # only untoggle bit if pause is called, not step
        if stepTime == None:
            self.paused = not self.paused

    def simulationTask(self, task):
        self.deltaTimeAccumulator += self._GlobalClock.getDt()
        while self.deltaTimeAccumulator > self.stepSize:
            self.deltaTimeAccumulator -= self.stepSize
            for agent in self.agents:
                agent.update(self.stepSize) 
        return task.cont 
    
    def _stopPhysics(self,task=None):
        print "[IsisWorld] Stopping Physical Simulator"
        taskMgr.remove("physics-SimulationTask")
        #base.disableParticles() 


    def _startPhysics(self, stopAt=None):
        """
        Here's another thing that's different than in the Panda Manual.
        I don't use the time accumulator to make the simulation run
        with a fixed time step, but instead I use the doMethodLater with
        task.again as the return value in self.simulationTask.

        This gave me better results than using the time accumulator method.
        """
        if stopAt != None:
          assert stopAt > 0.0
          assert stopAt > self.stepSize # cannot step less than physical simulator
          taskMgr.doMethodLater(stopAt, self._stopPhysics, "physics-SimulationStopper", priority=10)
          # or can you 
          taskMgr.doMethodLater(min(self.stepSize,stopAt), self.simulationTask, "physics-SimulationTask", priority=10)
        else:
          taskMgr.doMethodLater(self.stepSize, self.simulationTask, "physics-SimulationTask", priority=10)



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



def getCapsuleSize(collobj, radius=1):
    bounds = collobj.getTightBounds()
    # (max - min) bounds
    return [bounds[0][0], bounds[0][1], bounds[0][2], bounds[1][0], bounds[1][1], bounds[1][2], radius]
