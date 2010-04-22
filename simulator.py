"""
This is the simulator thread, which will take commands passed in from the xmlrpc thread and process them accordingly, potentially returning something to the
xmlrpc thread.

Created Jan 14, 2010
By Gleb Kuznetsov (glebk@mit.edu)
"""

#Debugging imports
# System Imports
import sys, time, math
#from direct.stdpy.threading import Thread, Lock
from threading import Thread, Lock # the panda3d threading modules don't work well

# Panda3d Imports
import direct.directbase.DirectStart
from pandac.PandaModules import DirectionalLight,AmbientLight,PointLight,Spotlight,OrthographicLens,PerspectiveLens,Fog
from pandac.PandaModules import Filename, loadPrcFileData
from pandac.PandaModules import CollisionTraverser,CollisionNode
from pandac.PandaModules import CollisionHandlerQueue,CollisionRay
from pandac.PandaModules import PandaNode,NodePath,Camera,TextNode
from pandac.PandaModules import CardMaker, NodePath, Point2, Point3
from pandac.PandaModules import VBase3,VBase4,Vec3,Vec4,BitMask32
from pandac.PandaModules import WindowProperties
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.actor.Actor import Actor
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.IntervalGlobal import Sequence, Parallel
from direct.interval.FunctionInterval import ParentInterval, Func
from direct.task import Task
from direct.gui.DirectGui import DirectLabel, DirectEntry
# HomeSim Imports
from visual.visual_object import Visual_Object
from xmlrpc.xmlrpc_server import HomeSim_XMLRPC_Server
from xmlrpc.command_handler import Command_Handler

#from pandac.PandaModules import OdeWorld
#myWorld = OdeWorld()
#myWorld.setGravity(0, 0, -9.81)

# stops vsync, which allows framerate to go past 60 FPS (capped at monitor's refresh rate)
loadPrcFileData("", "sync-video #f")


class Bar(NodePath):
        def __init__(self, scale=1, value=1, r=1, g=0, b=0):
                NodePath.__init__(self, 'healthbar')

                self.scale = scale
                cmfg = CardMaker('fg')
                cmfg.setFrame(- scale,  scale, -0.1 * scale, 0.1 * scale)
                self.fg = self.attachNewNode(cmfg.generate())

                cmbg = CardMaker('bg') 
                cmbg.setFrame(- scale, scale, -0.1 * scale, 0.1 * scale) 
                self.bg = self.attachNewNode(cmbg.generate()) 

                self.fg.setColor(r, g, b, 1) 
                self.bg.setColor(0.2, 0.2, 0.2, 1) 

                self.setValue(value) 

        def setValue(self, value): 
                value = min(max(0, value), 1) 
                self.fg.setScale(value * self.scale, 0, self.scale) 
                self.bg.setScale(self.scale * (1.0 - value), 0, self.scale) 
                self.fg.setX((value - 1) * self.scale * self.scale) 
                self.bg.setX(value * self.scale * self.scale) 

class ObjectGravitySimulator:
	"""
	"""
	falling_velocity = 10.0  # Z units per second
	
	def __init__(self, attach_object, object_bottom_buffer_distance = 0.1):
		#print "creating ObjectGravitySimulator for " + attach_object.name + ".\n"
		self.attach_object = attach_object
		self.object_bottom_buffer_distance = object_bottom_buffer_distance
		self.initialize_collision_handling()
	
	def initialize_collision_handling(self):
		self.collision_handling_mutex = Lock()
		
		self.cTrav = CollisionTraverser()
		
		self.groundRay = CollisionRay()
		self.groundRay.setOrigin(0,0,1000)
		self.groundRay.setDirection(0,0,-1)
		self.groundCol = CollisionNode(self.attach_object.name + "_collision_node")
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(0))
		self.groundCol.addSolid(self.groundRay)
		self.groundColNp = self.attach_object.render_model.attachNewNode(self.groundCol)
		self.groundHandler = CollisionHandlerQueue()
		self.cTrav.addCollider(self.groundColNp, self.groundHandler)
		
		# Uncomment this line to see the collision rays
		#self.groundColNp.show()
		
                #Uncomment this line to show a visual representation of the 
		#collisions occuring
                #self.cTrav.showCollisions(render)

	def destroy_collision_handling(self):
		self.collision_handling_mutex.acquire()
    
	def handle_collisions(self, seconds):
		self.collision_handling_mutex.acquire()
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(1))
		
		# Now check for collisions.
		self.cTrav.traverse(render)
		
		# Adjust the object's Z coordinate.  If the object's ray hit anything,
		# update its Z.
		
		current_z = self.attach_object.render_model.getZ() - self.object_bottom_buffer_distance
		entries = []
		for i in range(self.groundHandler.getNumEntries()):
			entry = self.groundHandler.getEntry(i)
			if (entry.getSurfacePoint(render).getZ() - 0.001 < current_z):
				entries.append(entry)

		entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
					     x.getSurfacePoint(render).getZ()))
		if (len(entries)>0):
			surface_z = entries[0].getSurfacePoint(render).getZ()
			#print "> " + self.attach_object.name + " is falling toward " + entries[0].getIntoNode().getName() + "\n"
			new_z = current_z - (self.falling_velocity * seconds)
			if (new_z < surface_z):
				new_z = surface_z
			if ((new_z > current_z + 0.00001) or (new_z < current_z - 0.00001)):
				self.attach_object.render_model.setZ(new_z + self.object_bottom_buffer_distance)
		
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(0))
		self.collision_handling_mutex.release()


	def step_simulation_time(self, seconds):
		#print "stepping object."
		self.handle_collisions(seconds)

class ObjectGravitySimulatorList:
	"""
	"""
	def __init__(self):
		self.attach_objects = []

	def add_attach_object(self, attach_object, object_bottom_buffer_distance=0):
		object_gravity_simulator = ObjectGravitySimulator(attach_object, object_bottom_buffer_distance=object_bottom_buffer_distance)
		self.attach_objects.append(object_gravity_simulator)
		return object_gravity_simulator

	def step_simulation_time(self, seconds):
		for attach_object in self.attach_objects:
			attach_object.step_simulation_time(seconds)

	def destroy_collision_handling(self):
		for attach_object in self.attach_objects:
			attach_object.destroy_collision_handling()

class FloatingCamera:
    """A floating 3rd person camera that follows an actor around, and can be
    turned left or right around the actor.

    Public fields:
    self.controlMap -- The camera's movement controls.
    actor -- The Actor object that the camera will follow.
    
    Public functions:
    init(actor) -- Initialise the camera.
    move(task) -- Move the camera each frame, following the assigned actor.
                  This task is called every frame to update the camera.
    setControl -- Set the camera's turn left or turn right control on or off.
    
    """
    

    def __init__(self,actor):
        """Initialise the camera, setting it to follow 'actor'.
        
        Arguments:
        actor -- The Actor that the camera will initially follow.
        
        """
        
        self.actor = actor
        self.prevtime = 0

        # The camera's controls:
        # "left" = move the camera left, 0 = off, 1 = on
        # "right" = move the camera right, 0 = off, 1 = on
        self.controlMap = {"left":0, "right":0}

        taskMgr.add(self.move,"cameraMoveTask")

        # Create a "floater" object. It is used to orient the camera above the
        # target actor's head.
        
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)


        base.disableMouse()
        base.camera.setPos(self.actor.getX(),self.actor.getY()+10,2)

        self.initialize_collision_handling()

    def initialize_collision_handling(self):
        # A CollisionRay beginning above the camera and going down toward the
        # ground is used to detect camera collisions and the height of the
        # camera above the ground. A ray may hit the terrain, or it may hit a
        # rock or a tree.  If it hits the terrain, we detect the camera's
        # height.  If it hits anything else, the camera is in an illegal
        # position.

        self.collision_handling_mutex = Lock()

        self.cTrav = CollisionTraverser()
        self.groundRay = CollisionRay()
        self.groundRay.setOrigin(0,0,1000)
        self.groundRay.setDirection(0,0,-1)
        self.groundCol = CollisionNode('camRay')
        self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(0))
        self.groundCol.addSolid(self.groundRay)
        self.groundColNp = base.camera.attachNewNode(self.groundCol)
        self.groundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.groundColNp, self.groundHandler)
        
        # Uncomment this line to see the collision rays
        #self.groundColNp.show()


    def handle_collisions(self):
        self.collision_handling_mutex.acquire()
	self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(1))

        # Now check for collisions.

        self.cTrav.traverse(render)

        # Keep the camera at one foot above the terrain,
        # or two feet above the actor, whichever is greater.
        
        entries = []
        for i in range(self.groundHandler.getNumEntries()):
            entry = self.groundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            base.camera.setZ(entries[0].getSurfacePoint(render).getZ()+1.0)
        if (base.camera.getZ() < self.actor.getZ() + 2.0):
            base.camera.setZ(self.actor.getZ() + 2.0)
        
	self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(0))
        self.collision_handling_mutex.release()
      
        
    def destroy_collision_handling(self):
        self.collision_handling_mutex.acquire()


    def move(self,task):
        """Update the camera's position before rendering the next frame.
        
        This is a task function and is called each frame by Panda3D. The
        camera follows self.actor, and tries to remain above the actor and
        above the ground (whichever is highest) while looking at a point
        slightly above the actor's head.
        
        Arguments:
        task -- A direct.task.Task object passed to this function by Panda3D.
        
        Return:
        Task.cont -- To tell Panda3D to call this task function again next
                     frame.
        
        """

        # FIXME: There is a bug with the camera -- if the actor runs up a
        # hill and then down again, the camera's Z position follows the actor
        # up the hill but does not come down again when the actor goes down
        # the hill.

        elapsed = task.time - self.prevtime

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.
         
        base.camera.lookAt(self.actor)
        camright = base.camera.getNetTransform().getMat().getRow3(0)
        camright.normalize()
        if (self.controlMap["left"]!=0):
            base.camera.setPos(base.camera.getPos() - camright*(elapsed*20))
        if (self.controlMap["right"]!=0):
            base.camera.setPos(base.camera.getPos() + camright*(elapsed*20))

        # If the camera is too far from the actor, move it closer.
        # If the camera is too close to the actor, move it farther.

        camvec = self.actor.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 5.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-5))
            camdist = 5.0
        if (camdist < 2.0):
            base.camera.setPos(base.camera.getPos() - camvec*(2-camdist))
            camdist = 2.0

        self.handle_collisions()

        # The camera should look in the player's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above the player's head.
        
        self.floater.setPos(self.actor.getPos())
        self.floater.setZ(self.actor.getZ() + 1.0)
        base.camera.lookAt(self.floater)

        # Store the task time and continue.
        self.prevtime = task.time
        return Task.cont

    def setControl(self, control, value):
        """Set the state of one of the camera's movement controls.
        
        Arguments:
        See self.controlMap in __init__.
        control -- The control to be set, must be a string matching one of
                   the strings in self.controlMap.
        value -- The value to set the control to.
        
        """

        # FIXME: this function is duplicated in FloatingCamera and Character, and
        # keyboard control settings are spread throughout the code. Maybe
        # add a Controllable class?
        
        self.controlMap[control] = value

class Character:

    """A character with an animated avatar that moves left, right or forward
       according to the controls turned on or off in self.controlMap.

    Public fields:
    self.controlMap -- The character's movement controls
    self.actor -- The character's Actor (3D animated model)

    Public functions:
    __init__ -- Initialise the character
    move -- Move and animate the character for one frame. This is a task
            function that is called every frame by Panda3D.
    setControl -- Set one of the character's controls on or off.

    """
    
    
    def __init__(self, agent_simulator, model, actions, startPos, scale):
        """Initialize the character.

        Arguments:
        model -- The path to the character's model file (string)
           run : The path to the model's run animation (string)
           walk : The path to the model's walk animation (string)
           startPos : Where in the world the character will begin (pos)
           scale : The amount by which the size of the model will be scaled 
                   (float)

           """

        self.agent_simulator = agent_simulator
	
        self.controlMap = {"turn_left":0, "turn_right":0, "move_forward":0, "move_backward":0,\
                           "look_up":0, "look_down":0, "look_left":0, "look_right":0}

        self.actor = Actor(model,actions)
        self.actor.reparentTo(render)
        self.actor.setScale(scale)
        self.actor.setPos(startPos)
        
        self.actor.setHpr(0,0,0)
    

        # Expose agent's right hand joint to attach objects to 
        self.actor_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'RightHand')
        self.actor_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'LeftHand')
        
        self.right_hand_holding_object = False
        self.left_hand_holding_object  = False

        # speech bubble
        self.last_spoke = 0
        self.speech_bubble=DirectLabel(parent=self.actor, text="", text_wordwrap=10, pad=(3,3), relief=None, text_scale=(.5,.5), pos = (0,0,6), frameColor=(.6,.2,.1,.5), textMayChange=1, text_frame=(0,0,0,1), text_bg=(1,1,1,1))
        self.speech_bubble.component('text0').textNode.setCardDecal(1)
        self.speech_bubble.setBillboardAxis()
        
        # visual processing
        self.actor_eye = self.actor.exposeJoint(None, 'modelRoot', 'LeftEyeLid')
        # put a camera on ralph
        self.fov = NodePath(Camera('RaphViz'))
        self.fov.reparentTo(self.actor_eye)
        self.fov.setHpr(180,0,0)
        #lens = OrthographicLens()
        #lens.setFilmSize(20,15)
        #self.fov.node().setLens(lens)
        lens = self.fov.node().getLens()
        lens.setFov(60) #  degree field of view (expanded from 40)
        lens.setNear(0.2)
        #self.fov.node().showFrustum() # displays a box around his head


        self.actor_neck = self.actor.controlJoint(None, 'modelRoot', 'Neck')
	
        # Define subpart of agent for when he's standing around
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])
        taskMgr.add(self.move,"moveTask") # Note: deriving classes DO NOT need
                                          # to add their own move tasks to the
                                          # task manager. If they override
                                          # self.move, then their own self.move
                                          # function will get called by the
                                          # task manager (they must then
                                          # explicitly call Character.move in
                                          # that function if they want it).
        self.prevtime = 0
        self.isMoving = False
	
        self.current_frame_count = 0.0
	
        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.
        
        self.initialize_collision_handling()

    def initialize_collision_handling(self):
        self.collision_handling_mutex = Lock()
        
        self.cTrav = CollisionTraverser()
        
        self.groundRay = CollisionRay()
        self.groundRay.setOrigin(0,0,1000)
        self.groundRay.setDirection(0,0,-1)
        self.groundCol = CollisionNode('ralphRay')
        self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(0))
        self.groundCol.addSolid(self.groundRay)
        self.groundColNp = self.actor.attachNewNode(self.groundCol)
        self.groundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.groundColNp, self.groundHandler)

        # Uncomment this line to see the collision rays
        # self.groundColNp.show()

        #Uncomment this line to show a visual representation of the 
        #collisions occuring
        # self.cTrav.showCollisions(render)

    def destroy_collision_handling(self):
        self.collision_handling_mutex.acquire()
    
    def handle_collisions(self):
        self.collision_handling_mutex.acquire()
        self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(1))

        # Now check for collisions.
        self.cTrav.traverse(render)
        
        # Adjust the character's Z coordinate.  If the character's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.
        
        entries = []
        for i in range(self.groundHandler.getNumEntries()):
            entry = self.groundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            self.actor.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.actor.setPos(self.startpos)
        
        self.groundCol.setIntoCollideMask(BitMask32.bit(0))
        self.groundCol.setFromCollideMask(BitMask32.bit(0))
        self.collision_handling_mutex.release()

    def position(self):
        return self.actor.getPos()
	
    def forward_normal_vector(self):
        backward = self.actor.getNetTransform().getMat().getRow3(1)
        backward.setZ(0)
        backward.normalize()
        return -backward

    def step_simulation_time(self, seconds):
        # save the character's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        self.startpos = self.actor.getPos()

        def bound(i, mn = -1, mx = 1): return min(max(i, mn), mx) # enforces bounds on a numeric value
        # move the character if any of the move controls are activated.

        if (self.controlMap["turn_left"]!=0):
            self.actor.setH(self.actor.getH() + seconds*30)
        if (self.controlMap["turn_right"]!=0):
            self.actor.setH(self.actor.getH() - seconds*30)
        if (self.controlMap["move_forward"]!=0):
            self.actor.setPos(self.actor.getPos() + self.forward_normal_vector() * (seconds*0.5))
        if (self.controlMap["move_backward"]!=0):
            self.actor.setPos(self.actor.getPos() - self.forward_normal_vector() * (seconds*0.5))
        if (self.controlMap["look_left"]!=0):
            self.actor_neck.setP(bound(self.actor_neck.getP(),-60,60)+1*(seconds*50))
        if (self.controlMap["look_right"]!=0):
            self.actor_neck.setP(bound(self.actor_neck.getP(),-60,60)-1*(seconds*50))
        if (self.controlMap["look_up"]!=0):
            self.actor_neck.setH(bound(self.actor_neck.getH(),-60,80)+1*(seconds*50))
        if (self.controlMap["look_down"]!=0):
            self.actor_neck.setH(bound(self.actor_neck.getH(),-60,80)-1*(seconds*50))

        # allow dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += seconds
        self.speech_bubble['text_bg']=(1,1,1,1/(2*self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(2*self.last_spoke+0.01))
        if self.last_spoke > 2:
            self.speech_bubble['text'] = ""

        # If the character is moving, loop the run animation.
        # If he is standing still, stop the animation.
	
        if (self.controlMap["move_forward"]!=0) or (self.controlMap["move_backward"]!=0):
            if self.isMoving is False:
                self.isMoving = True
        else:
            if self.isMoving:
                self.current_frame_count = 5.0
                self.isMoving = False
	
	total_frame_num = self.actor.getNumFrames('walk')
	if self.isMoving:
		self.current_frame_count = self.current_frame_count + (seconds*10.0)
		while (self.current_frame_count >= total_frame_num + 1):
			self.current_frame_count -= total_frame_num
		while (self.current_frame_count < 0):
			self.current_frame_count += total_frame_num
	self.actor.pose('walk', self.current_frame_count)
	
        self.handle_collisions()

    def move(self, task):
        """Move and animate the character for one frame.

        This is a task function that is called every frame by Panda3D.
        The character is moved according to which of it's movement controls
        are set, and the function keeps the character's feet on the ground
        and stops the character from moving if a collision is detected.
        This function also handles playing the characters movement
        animations.

        Arguments:
        task -- A direct.task.Task object passed to this function by Panda3D.

        Return:
        Task.cont -- To tell Panda3D to call this task function again next
                     frame.
        """

        elapsed = task.time - self.prevtime

        # Store the task time and continue.
        self.prevtime = task.time
        return Task.cont
    
    def setControl(self, control, value):
        """Set the state of one of the character's movement controls.

        Arguments
        See self.controlMap in __init__.
        control -- The control to be set, must be a string matching one of
                   the strings in self.controlMap.
        value -- The value to set the control to.

        """

        # FIXME: this function is duplicated in Camera and Character, and
        # keyboard control settings are spread throughout the code. Maybe
        # add a Controllable class?

        self.controlMap[control] = value

    # these are simple commands that can be exported over xml-rpc (or attached to the keyboard)


    def get_objects(self):
        """ Looks up all of the model nodes that are 'isInView' of the camera
        and returns them in the in_view dictionary (as long as they are also
        in the self.world_objects -- otherwise this includes points defined
        within the environment/terrain). 

        TODO:  1) include more geometric information about the object (size, mass, etc)
        """

        def map3dToAspect2d(node, point):
            """Maps the indicated 3-d point (a Point3), which is relative to 
            the indicated NodePath, to the corresponding point in the aspect2d 
            scene graph. Returns the corresponding Point3 in aspect2d. 
            Returns None if the point is not onscreen. """ 
            # Convert the point to the 3-d space of the camera 
            p3 = self.fov.getRelativePoint(node, point) 

            # Convert it through the lens to render2d coordinates 
            p2 = Point2()
            if not self.fov.node().getLens().project(p3, p2):
                return None 
            r2d = Point3(p2[0], 0, p2[1])
            # And then convert it to aspect2d coordinates 
            a2d = aspect2d.getRelativePoint(render2d, r2d)
            return a2d

        objs = render.findAllMatches("**/+ModelNode")
        in_view = {}
        for o in objs:
            o.hideBounds() # in case previously turned on
            o_pos = o.getPos(self.fov)
            if self.fov.node().isInView(o_pos):
                if self.agent_simulator.world_objects.has_key(o.getName()):
                    b_min, b_max =  o.getTightBounds()
                    a_min = map3dToAspect2d(render, b_min)
                    a_max = map3dToAspect2d(render, b_max)
                    if a_min == None or a_max == None:
                        continue
                    x_diff = math.fabs(a_max[0]-a_min[0])
                    y_diff = math.fabs(a_max[2]-a_min[2])
                    area = 100*x_diff*y_diff  # percentage of screen
                    object_dict = {'x_pos': (a_min[2]+a_max[2])/2.0,\
                                   'y_pos': (a_min[0]+a_max[0])/2.0,\
                                   'distance':o.getDistance(self.fov), \
                                   'area':area,\
                                   'orientation': o.getH(self.fov)}
                    in_view[o.getName()]=object_dict
                    print o.getName(), object_dict
        return in_view

    def control__turn_left__start(self):
        self.setControl("turn_left",  1)
        self.setControl("turn_right", 0)

    def control__turn_left__stop(self):
        self.setControl("turn_left",  0)

    def control__turn_right__start(self):
        self.setControl("turn_left",  0)
        self.setControl("turn_right", 1)

    def control__turn_right__stop(self):
        self.setControl("turn_right", 0)

    def control__move_forward__start(self):
        self.setControl("move_forward",  1)
        self.setControl("move_backward", 0)

    def control__move_forward__stop(self):
        self.setControl("move_forward",  0)

    def control__move_backward__start(self):
        self.setControl("move_forward",  0)
        self.setControl("move_backward", 1)

    def control__move_backward__stop(self):
        self.setControl("move_backward", 0)

    def control__look_left__start(self):
        self.setControl("look_left",  1)
        self.setControl("look_right", 0)

    def control__look_left__stop(self):
        self.setControl("look_left",  0)

    def control__look_right__start(self):
        self.setControl("look_right",  1)
        self.setControl("look_left", 0)

    def control__look_right__stop(self):
        self.setControl("look_right",  0)

    def control__look_up__start(self):
        self.setControl("look_up",  1)
        self.setControl("look_down", 0)

    def control__look_up__stop(self):
        self.setControl("look_up",  0)
    
    def control__look_down__start(self):
        self.setControl("look_down",  1)
        self.setControl("look_up",  0)
    
    def control__look_down__stop(self):
        self.setControl("look_down",  0)

    def can_grasp(self, object_name):
        objects = self.get_objects()
        if objects.has_key(object_name):
            object_view = objects[object_name]
            distance = object_view['distance']
            if (distance < 5.0):
                return True
        return False

    def control__say(self, message):
       self.speech_bubble['text'] = message
       self.last_spoke = 0

    def control__pick_up_with_right_hand(self, pick_up_object):
        print "attempting to pick up " + pick_up_object + " with right hand.\n"
        if self.right_hand_holding_object:
            return 'right hand is already holding ' + self.right_hand_holding_object.getName() + '.'
	if self.can_grasp(pick_up_object):
	    world_object = self.agent_simulator.world_objects[pick_up_object]
	    object_parent = world_object.getParent()
	    if (object_parent == self.agent_simulator.env):
		world_object.wrtReparentTo(self.actor_right_hand)
		world_object.setPos(0, 0, 0)
		world_object.setHpr(0, 0, 0)
		self.right_hand_holding_object = world_object
		return 'success'
	    else:
		return 'object (' + pick_up_object + ') is already held by something or someone.'
	else:
	    return 'object (' + pick_up_object + ') is not graspable (i.e. in view and close enough).'

    def put_object_in_empty_left_hand(self, object_name):
	if (self.left_hand_holding_object is not False):
	    return False
	world_object = self.agent_simulator.world_objects[object_name]
	world_object.wrtReparentTo(self.actor_left_hand)
	world_object.setPos(0, 0, 0)
	world_object.setHpr(0, 0, 0)
	self.left_hand_holding_object = world_object
	return True
    
    def control__pick_up_with_left_hand(self, pick_up_object):
        print "attempting to pick up " + pick_up_object + " with left hand.\n"
        if self.left_hand_holding_object:
            return 'left hand is already holding ' + self.left_hand_holding_object.getName() + '.'
        if self.can_grasp(pick_up_object):
	    world_object = self.agent_simulator.world_objects[pick_up_object]
	    object_parent = world_object.getParent()
	    if (object_parent == self.agent_simulator.env):
		self.put_object_in_empty_left_hand(pick_up_object)
		return 'success'
	    else:
		return 'object (' + pick_up_object + ') is already held by something or someone.'
        else:
            return 'object (' + pick_up_object + ') is not graspable (i.e. in view and close enough).'

    def control__drop_from_right_hand(self):
        print "attempting to drop object from right hand.\n"
        if self.right_hand_holding_object is False:
            return 'right hand is not holding an object.'
        world_object = self.right_hand_holding_object
        self.right_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.env)
        world_object.setHpr(0, 0, 0)
        world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'
    
    def control__drop_from_left_hand(self):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is False:
            return 'left hand is not holding an object.'
        world_object = self.left_hand_holding_object
        self.left_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.env)
        world_object.setHpr(0, 0, 0)
        world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
	return 'success'

    def is_holding(self, object_name):
	return ((self.left_hand_holding_object  and (self.left_hand_holding_object.getName()  == object_name)) or
		(self.right_hand_holding_object and (self.right_hand_holding_object.getName() == object_name)))
    
    def empty_hand(self):
        if (self.left_hand_holding_object is False):
            return self.actor_left_hand
        elif (self.right_hand_holding_object is False):
            return self.actor_right_hand
        return False

    def has_empty_hand(self):
        return (self.empty_hand() is not False)

    def control__use_object_with_object(self, use_object, with_object):
	if ((use_object == 'knife') and (with_object == 'loaf_of_bread')):
	    if self.is_holding('knife'):
		if self.can_grasp('loaf_of_bread'):
		    if self.has_empty_hand():
			empty_hand      = self.empty_hand()
			new_object_name = self.agent_simulator.create_object__slice_of_bread([float(x) for x in empty_hand.getPos()])
			if (empty_hand == self.actor_left_hand):
			    self.put_object_in_empty_left_hand(new_object_name)
			elif (empty_hand == self.actor_right_hand):
			    self.put_object_in_empty_right_hand(new_object_name)
			else:
			    return "simulator error: empty hand is not left or right.  (are there others?)"
			return 'success'
		    else:
			return 'failure: one hand must be empty to hold loaf_of_bread in place while using knife.'
		else:
		    return 'failure: loaf of bread is not graspable (in view and close enough)'
	    else:
		return 'failure: must be holding knife object to use it.'
        return 'failure: don\'t know how to use ' + use_object + ' with ' + with_object + '.'

class Simulator(DirectObject):
    
    # constants
    try:
        font=loader.loadFont('models/cmss12.egg')
    except:
        font = TextNode.getDefaultFont()

    HOME_POSITION = VBase3(0, 0, 0)
    
    # variables
    object_gravity_simulator_list = ObjectGravitySimulatorList()
    
    paused = 1 # begin in a paused state by default
    
    #Macro-like function used to reduce the amount to code needed to create the
    #on screen instructions
    def genLabelText(self, text, i):
        return OnscreenText(text = text, pos = (-1.3, .95-.05*i),\
                            fg=(1,1,1,1), align = TextNode.ALeft,\
                            scale = .05, \
                            font = self.font,\
                            mayChange=True)

    def get_camera_position(self):
        print base.camera.getPos()
        print base.camera.getHpr()

    def get_agent_position(self):
        x,y,z = self.agent.actor.getPos()
        h,p,r = self.agent.actor.getHpr()
        nh,np,nr = self.agent.actor_neck.getHpr()
        left_hand_obj = "" 
        right_hand_obj = "" 
        if self.agent.left_hand_holding_object:  left_hand_obj = self.agent.left_hand_holding_object.getName()
        if self.agent.right_hand_holding_object: right_hand_obj = self.agent.right_hand_holding_object.getName()
        return {'body_x': x, 'body_y': y, 'body_z': z,'body_h':h,\
                'body_p': p, 'body_r': r, 'neck_h':nh,'neck_p':np,'neck_r':nr, 'in_left_hand': left_hand_obj, 'in_right_hand':right_hand_obj}
    
    def get_agent_vision(self):
        # TODO: not yet implemented (needs to print out and read image from camera)
        return []# str(self.agent.fov.node().getCameraMask())

    def get_objects(self):
        return self.agent.get_objects()

    def get_utterances(self):
        """ Clear out the buffer of things that the teacher has typed,
        FIXME: perpahs these should be timestamped if they are not 
         at the right time? """
        utterances = self.teacher_utterances
        self.teacher_utterances = []
        return utterances


    def print_objects(self):
        text = "Objects in FOV: "+ ", ".join(self.get_objects().keys())
        self.objectText.setText(text)

    def user_requests_quit(self):
        print "\nUser has requested to quit.  Preparing to exit Commonsense Simulator.\n";
        # For some reason Linux locks up sometimes if we simply use sys.exit.
        # Perhaps we need to shut down other threads or mutex certain Panda3D functions?
        # Collision detection also seems like it might cause the problem (so make sure to not be detecting collisions when calling sys.exit)
        # For now, this user_requests_quit function seems to help.
        #print "\nShutting down agent collision handling.\n";
        self.agent.destroy_collision_handling()
        self.camera.destroy_collision_handling()
        self.object_gravity_simulator_list.destroy_collision_handling()
        #print "\nExiting now.\n";
        sys.exit()

    # Panda3D threads do not leave enough time for other threads to run, so this sleeps a little at every frame.
    def initialize_simulator_relax_thread_task(self):
        def simulator_relax_thread_task(task):
            time.sleep(0.00001)
            return task.cont
        taskMgr.add(simulator_relax_thread_task,"simulator_relax_thread_task")

    def toggle_paused(self):
        self.paused = 1 - self.paused

    def move(self, task):
        if self.paused == 0:
            self.step_simulation_time(0.01)
        time.sleep(0.001)
        return task.cont


    def __init__(self):
        """ Initializes the Simulator object """


        props = WindowProperties( )
        props.setTitle( 'IsisWorld v0.3' )
        base.win.requestProperties( props )
        # initialize GUI components 
        self.title = OnscreenText(text="IsisWorld",
                              style=1, fg=(0,1,1,1), font = self.font,
                              pos=(0.85,0.95,1), scale = .07)
        self.escapeEventText = self.genLabelText("ESC: quit", 0)
        self.instuctText_3   = self.genLabelText("a,s: Rotate world camera", 1)
        self.pauseEventText  = self.genLabelText("p: (un)pause; SPACE advances simulator one time step.",2)
        self.instuctText_1   = self.genLabelText("up,down,left,right: to control Ralph's direction", 3)
        self.instuctText_2   = self.genLabelText("h,j,k,l: to control Ralph's head orientation", 4)
        self.objectText      = self.genLabelText("o: display objects in Ralph's visual field", 5)
       
        self.teacher_utterances = [] # last message typed
        # main dialogue box
        def disable_keys(x):
            # print "disabling"
            x.command_box.enterText("")
            x.command_box.suppressKeys=True
            x.command_box["frameColor"]=(0.631, 0.219, 0.247,1)

        def enable_keys(x):
            # print "enabling"
            x.command_box["frameColor"]=(0.631, 0.219, 0.247,.25)
            x.command_box.suppressKeys=False

        def accept_message(message,x):
            x.teacher_utterances.append(message)
            x.command_box.enterText("")
            

        #text_fg=((.094,0.137,0.0039,1),
        self.command_box = DirectEntry(pos=(-1.2,-0.95,-0.95), text_fg=(0.282, 0.725, 0.850,1), frameColor=(0.631, 0.219, 0.247,0.25), suppressKeys=1, initialText="enter text and hit return", enableEdit=0,scale=0.07, focus=0, focusInCommand=disable_keys, focusOutCommand=enable_keys, focusInExtraArgs=[self], focusOutExtraArgs=[self], command=accept_message, extraArgs=[self], entryFont=self.font,  width=15, numLines=1)
        #base.win.setColor(0.5,0.8,0.8)
        base.win.setClearColor(Vec4(0,0,0,1))
	
        self.initialize_simulator_relax_thread_task()
        

        # setup terrain
        self.env = loader.loadModel("models/world/world")
        self.env.reparentTo(render)
        self.env.setPos(0,0,0)
        self.env.setCollideMask(BitMask32.bit(1))
        self.env.setColor(0.5,0.8,0.8)
        render.showBounds()
        
        #self.goal_sleep = Bar(100,1)
        #self.goal_sleep.reparentTo(render)

        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.6, 0.6, 0.6, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(-60, -60, 0)
        render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor(VBase4(1.0, 1.0, 1.0, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
	
        self.agent = Character(self, "models/ralph/ralph", {"walk":"models/ralph/ralph-walk", "run": "models/ralph/ralph-run"}, VBase3(6, 2, 0), .2)

        self.agent.control__say("Hi, I'm Ralph. Please build me.")
        ### Set up displays and cameras ###
        self.camera = FloatingCamera(self.agent.actor)
        # set up picture in picture
        dr = base.camNode.getDisplayRegion(0)
        aspect_ratio = 16.0 / 9.0
        window = dr.getWindow()
        pip_size = 0.40 # percentage of width of screen
        dr_pip = window.makeDisplayRegion(1-pip_size,1,0,(1.0 / aspect_ratio) * float(dr.getPixelWidth())/float(dr.getPixelHeight()) * pip_size)
        dr_pip.setCamera(self.agent.fov)
        dr_pip.setSort(dr.getSort())
        dr_pip.setClearColor(VBase4(0, 0, 0, 1))
        dr_pip.setClearColorActive(True)
        dr_pip.setClearDepthActive(True)
        #self.agent.fov.node().getLens().setAspectRatio(aspect_ratio)
        dr_pip.setActive(1)
	
        ## SET UP I/O ##
        base.disableMouse()
        # Accept some keys to move the camera.
        self.accept("a-up", self.camera.setControl, ["right", 0])
        self.accept("a",    self.camera.setControl, ["right", 1])
        self.accept("s-up", self.camera.setControl, ["left",  0])
        self.accept("s",    self.camera.setControl, ["left",  1])
        # control keys to move the character
        self.accept("arrow_left",     self.agent.control__turn_left__start,     [])
        self.accept("arrow_left-up",  self.agent.control__turn_left__stop,      [])
        self.accept("arrow_right",    self.agent.control__turn_right__start,    [])
        self.accept("arrow_right-up", self.agent.control__turn_right__stop,     [])
        self.accept("arrow_up",       self.agent.control__move_forward__start,  [])
        self.accept("arrow_up-up",    self.agent.control__move_forward__stop,   [])
        self.accept("arrow_down",     self.agent.control__move_backward__start, [])
        self.accept("arrow_down-up",  self.agent.control__move_backward__stop,  [])
        # head movement controls (vi direction map)  
        self.accept("k",              self.agent.control__look_up__start, [])
        self.accept("k-up",           self.agent.control__look_up__stop, [])
        self.accept("j",              self.agent.control__look_down__start, [])
        self.accept("j-up",           self.agent.control__look_down__stop, [])
        self.accept("h",              self.agent.control__look_left__start, [])
        self.accept("h-up",           self.agent.control__look_left__stop, [])
        self.accept("l",              self.agent.control__look_right__start, [])
        self.accept("l-up",           self.agent.control__look_right__stop, [])
        # key input
        self.accept("escape", self.user_requests_quit)
        self.accept("space",  self.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("o", self.print_objects) # displays objects in field of view 
        self.accept("p", self.toggle_paused)
        self.accept("r", self.reset_simulation)

        taskMgr.add(self.move,"moveTask") # Note: deriving classes DO NOT need
	
        # xmlrpc server command handler
        xmlrpc_command_handler = Command_Handler(self)
	
        # xmlrpc server
        self.server_object = HomeSim_XMLRPC_Server()
        self.server = self.server_object.server
        self.server.register_function(xmlrpc_command_handler.command_handler,'do')
        self.server_thread = Thread(group=None, target=self.server.serve_forever, name='xmlrpc')
        self.server_thread.start()
        
	
        self.reset_simulation()
        

    def reset_simulation(self):
        # store place for objects in the world
        self.world_objects = {}
	
        self.create_object__counter(           [5,      0, 3])
        self.create_object__knife(             [4.0, -0.1, 4])
        #self.create_object__toaster(           [4.5, -0.3, 4])
        self.create_object__toaster_with_bread([4.5, -0.3, 4])
        self.create_object__loaf_of_bread(     [4.2,  0.5, 4])
        self.create_object__piece_of_toast(    [5,   -0.3, 4])
        
        # performance
        #render.analyze()

        ### TESTING ###

        self.step_simulation_time(0)
	
    # keyboard handler functions
    
    def keyboard__arrow_left(self):
	self.agent.control__turn_left__start()

    def keyboard__arrow_left__up(self):
	self.agent.control__turn_left__stop()

    # object creation functions with standard sizes and other parameters
    
    def create_object__counter(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'counter', position, model='models/kitchen_models/Counter')
	self.put_object_in_world(new_object, scale=0.2)
	return new_object.name

    def create_object__knife(self, position=[0.0, 0.0, 0.0]):
	new_object = Visual_Object(0, 'knife', position, model='models/kitchen_models/knife')
	self.put_object_in_world(new_object, scale=0.004, object_bottom_buffer_distance = 0.03)
	return new_object.name

    def create_object__slice_of_bread(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'slice_of_bread', position, model='models/kitchen_models/slice_of_bread')
	self.put_object_in_world(new_object, scale=0.2, object_bottom_buffer_distance = 0.02)
	return new_object.name

    def create_object__toaster(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'toaster', position, model='models/kitchen_models/toaster')
	self.put_object_in_world(new_object, scale=0.2, object_bottom_buffer_distance = 0.1)
	return new_object.name

    def create_object__toaster_with_bread(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'toaster_with_bread', position, model='models/kitchen_models/toaster_with_bread')
	self.put_object_in_world(new_object, scale=0.2, object_bottom_buffer_distance = 0.1)
	return new_object.name

    def create_object__loaf_of_bread(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'loaf_of_bread', position, model='models/kitchen_models/loaf_of_bread')
	self.put_object_in_world(new_object, scale=0.07,  object_bottom_buffer_distance = 0.08)
	return new_object.name

    def create_object__piece_of_toast(self, position=[0.0, 0.0, 0.0]):
        new_object = Visual_Object(0, 'piece_of_toast', position, model='models/kitchen_models/piece_of_toast')
	self.put_object_in_world(new_object, scale=0.2, object_bottom_buffer_distance = 0.02)
	return new_object.name

    def step_simulation_time(self, seconds):
        self.object_gravity_simulator_list.step_simulation_time(seconds)
        self.agent.step_simulation_time(seconds)

    def step_simulation(self, seconds):
        #print "stepping simulation %f seconds.\n" % (seconds)
        self.step_simulation_time(seconds)
        
    # Methods to Place Objects in World 
    def put_object_in_world(self, visual_object, parent=None, scale=1.0, rotate_x=0, simulate_gravity=1, object_bottom_buffer_distance=0):
        """
        Given a visual object make an instance of it in the simulator world.
        For now, visual object has only a position attribute.
        
        visual_object must be of type Visual_Object
        
        Returns name representing object handle.
        """
        visual_object.simulate_gravity = simulate_gravity
        if visual_object.name in self.world_objects:
            visual_object.duplicate_name() # add 2 or 3 or whatever
        
        visual_object.render_model = loader.loadModel(visual_object.model)
        visual_object.render_model.setName(visual_object.name)
        visual_object.render_model.setCollideMask(BitMask32.bit(1))
        if simulate_gravity:
	    visual_object.gravity_simulator = self.object_gravity_simulator_list.add_attach_object(visual_object, object_bottom_buffer_distance=object_bottom_buffer_distance)
        # add into rendering tree
        if parent==None:
            # add to second to topmost visual node, the environment
            visual_object.render_model.reparentTo(self.env)
        else:
            # look up visual object node
            visual_object.render_model.reparentTo(self.world_objects[parent.name])
        # set position 
        apply(visual_object.render_model.setPos, visual_object.position)
        # set name
        self.world_objects[visual_object.name] = visual_object.render_model
        if scale != 1.0:
            visual_object.render_model.setScale(scale)
        if rotate_x != 0:
            # rotate x degrees
            visual_object.render_model.setHpr(rotate_x,0,0)
        # enable collision detection
        return visual_object.name


# cannot check if name == '__main__', because does not work when run with p3d file
# begin simulator
a = Simulator()
run()


    

