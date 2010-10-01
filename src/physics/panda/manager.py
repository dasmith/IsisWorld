from direct.showbase import DirectObject
from pandac.PandaModules import * # TODO: specialize
# initialize collision mask constants  
FLOORMASK = BitMask32.bit(1)      
WALLMASK = BitMask32.bit(2)
PICKMASK = BitMask32.bit(3)
AGENTMASK = BitMask32.bit(4)
OBJMASK= BitMask32.bit(5)
OBJFLOOR = BitMask32.bit(6)
OBJPICK = BitMask32.bit(7)
OBJSIDE = BitMask32.bit(8)

#from ..utils import *

class PhysicsWorldManager(DirectObject.DirectObject):
    
    def __init__(self,world):
        """ Initialize the 3 Collision Handlers and the base Traverser, which looks
        through the entire node path. 
        
        Future optimization: traversers that only look at certain branches of the render tree.
        """
        self._GlobalClock=ClockObject.getGlobalClock() 
        globalClock.setMode(ClockObject.MLimited) 
        globalClock.setFrameRate(20)
        self._FrameTime=self._GlobalClock.getFrameTime() 
        self._GlobalClock.setRealTime(self._FrameTime) 
        
        self.world = world # only used by sky task. 
               
        self.stepping = False
        # keep track of all agents
        self.agents = []

        # Initialize the collision traverser.
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True) 
        
        # this handler is used by ISISOBJECTS only, Ralphs have their own Gravity Handlers.
        self.cFloor = CollisionHandlerGravity()
        # gravity should be -9.81m/s, but that doesn't quite work
        self.cFloor.setGravity(100)
        self.cFloor.setOffset(.5)
        self.cFloor.setReach(3)
        self.cFloor.setMaxVelocity(1)
        # initialize 3 handlers: wall, gravity, and other events
        
        # the CollisionHandlerPusher is good for keeping items from going through walls
        self.cWall = CollisionHandlerPusher()
        self.cWall.setHorizontal(True)
        # this tracks the velocity of moving objects, whereas CollisionHandlerFloor doesnt

        self.cWallO = CollisionHandlerFluidPusher()
        self.cWallO.setHorizontal(True)

        # Initialize the handler.
        base.cEvent = CollisionHandlerEvent()
        base.cEvent.addInPattern("%fn-into-%(container)it")
        base.cEvent.addInPattern("%fn-into-%(surface)it")
        base.cEvent.addInPattern('%fn-into-%in')
        base.cEvent.addOutPattern("%fn-outof-%(container)it")
        base.cEvent.addOutPattern("%fn-outof-%(surface)it")
        base.cEvent.addOutPattern('%fn-outof-%in')
       
        # initialize listeners
        base.accept('object-into-acontainer', self._enterContainer)
        base.accept('object-outof-acontainer', self._exitContainer)
        base.accept('object-into-asurface', self._exitSurface)
        base.accept('object-outof-asurface', self._exitSurface)
        #base.accept('object-into-object', self._objCollisionHandlerIn)
        #base.accept('object-outof-object', self._objCollisionHandlerOut)
        base.accept('agent-into-object', self._agentCollisionHandlerIn)
        base.accept('agent-into-agent', self._agentsCollisionIn)

        # start it up 
        self.paused = True
        self._startPhysics()


    def _enterContainer(self, entry):
        """ When an object enters into a container. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterContainer(cInto)
        print "Entering container %s, %s" % (cFrom, cInto)

    def _exitContainer(self, entry):
        """ When an object exits a container."""
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterContainer(cInto)
        print "Exiting container %s, %s" % (cFrom, cInto)

    def _enterSurface(self, entry):
        """ When an object collides with another object's surface plane. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterSurface(cInto)
        print "Entering surface %s, %s" % (cFrom, cInto)

    def _exitSurface(self, entry):
        """ When an object ceases to collide with another object's surface plane. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterSurface(cInto)
        print "Exiting surface %s, %s" % (cFrom, cInto)

    def _objCollisionHandlerIn(self, entry):
        """ The general case when two objects collide"""
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        
        if hasattr(cInto,'enterContainer'):
            cInto.enterContainer(cInto)
        print "Object In Collision: %s, %s" % (cFrom, cInto)
    
    def _objCollisionHandlerOut(self, entry):
        """ The general caase when two objects cease to collide """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        if hasattr(cInto,'exitContainer'):
            cInto.exitContainer(cInto)
        print "Object Out Collision: %s, %s" % (cFrom, cInto)

    def _agentCollisionHandlerIn(self, entry):
        """ When an agent collides with a container object. """
        agent = entry.getFromNodePath().getParent()
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        if hasattr(cInto,'enterContainer'):
            cInto.enterContainer(agent)
        print "Agent In Collision: %s, %s" % (agent, cInto)

    def _agentsCollisionIn(self, entry):
        """ When two agents collide with each other. """
        agentFrom = entry.getFromNodePath().getParent()
        agentInto = entry.getIntoNodePath().getParent()
        print "Agents collided : %s, %s" % (agentFrom, agentInto) 

        
    def stepSimulation(self,stepTime=1):
        if self.paused:
            self.resume(stepTime)
        else:
            print "Error, cannot step while simulator is running"
 
    def stopSimulation(self):
         if not self.paused: 
             #self._GlobalClock.setMode(ClockObject.MSlave)
             print "[IsisWorld] Pausing Simulator"
             self._stopPhysics()
             self.paused = True

    def startSimulation(self,stepTime=None):
        if self.paused: 
            #self._GlobalClock.setMode(ClockObject.MNormal) 
            self._startPhysics(stepTime)
            if stepTime == None:
                print "[IsisWorld] Restarting Simulator"
                self.paused = False
            else:
                print "[IsisWorld] Stepping Simulator"

    def togglePaused(self,stepTime=None):
        if self.paused:
            self.resume(stepTime)
        else:
            self.pause()
            
    def simulationTask(self, task):
        self.commandHandler.panda3d_thread_process_command_queue()
        dt = self._GlobalClock.getDt()
        for agent in self.agents:
            agent.update(dt) 
        return task.cont 
    
    def _stopPhysics(self,task=None):
        taskMgr.remove("visual-movingClouds")
        taskMgr.remove("physics-SimulationTask")
        self.stepping = False

    def _startPhysics(self, stepTime=None):
        if stepTime != None:
            assert stepTime >= 0.01
            # Adujust for delays to better approximate the right stopping time
            if stepTime >= .015:
                stepTime -= .005
            taskMgr.doMethodLater(stepTime, self._stopPhysics, "physics-SimulationStopper", priority=10)
            # or can you
            self.stepping = True
        taskMgr.add(self.world.updateSkyTask, "visual-movingClouds")
        taskMgr.add(self.simulationTask, "physics-SimulationTask", priority=10)
