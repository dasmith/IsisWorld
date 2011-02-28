import math, random, os
from time import time

import direct.directbase.DirectStart 
from direct.showbase.DirectObject import DirectObject 
from direct.actor.Actor import Actor 
from direct.task import Task 
from direct.gui.OnscreenImage import OnscreenImage
from direct.controls.ControlManager import CollisionHandlerRayStart
from pandac.PandaModules import CollisionTraverser 
from pandac.PandaModules import ActorNode

from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import DirectLabel
from pandac.PandaModules import PandaNode, NodePath, TransparencyAttrib

import platform
# project stuff
from ..actions.actions import *
from ..physics.ode.kcc import kinematicCharacterController
from ..physics.ode.odeWorldManager import *
from ..utilities import frange
from ..utilities import pnm_image__as__xmlrpc_image
from ..utilities import rgb_ram_image__as__xmlrpc_image

class IsisAgent(kinematicCharacterController,DirectObject):
    
    @classmethod
    def set_physics(cls,physics):
        """ This method is set in src.loader when the generators are loaded
        into the namespace.  This frees the environment definitions (in 
        scenario files) from having to pass around the physics parameter 
        that is required for all IsisObjects """
        cls.physics = physics

    def __init__(self, name, position=None, queueSize = 100):
        # load the model and the different animations for the model into an Actor object.
        self.actor= Actor("media/models/boxman",
                          {"walk":"media/models/boxman-walk", 
                           "idle": "media/models/boxman-idle"})
        self.actor.setScale(1.0)
        self.actor.setH(0)
        #self.actor.setLODAnimation(10,5,2) # slows animation framerate when actor is far from camera, if you can figure out reasonable params
        self.actor.setColorScale(random.random(), random.random(), random.random(), 1.0)
        self.actorNodePath = NodePath('agent-%s' % name)
        self.activeModel = self.actorNodePath
        
        
        self.actorNodePath.reparentTo(render)
        
        self.actor.reparentTo(self.actorNodePath)
        self.name = name
        self.isMoving = False
        
        # initialize ODE controller
        kinematicCharacterController.__init__(self, IsisAgent.physics, self.actorNodePath)
        self.setGeomPos(self.actorNodePath.getPos(render))
        """
        Additional Direct Object that I use for convenience.
        """
        self.specialDirectObject = DirectObject()

        """
        How high above the center of the capsule you want the camera to be
        when walking and when crouching. It's related to the values in KCC.
        """
        self.walkCamH = 0.7
        self.crouchCamH = 0.2
        self.camH = self.walkCamH

        """
        This tells the Player Controller what we're aiming at.
        """
        self.aimed = None

        self.isSitting = False
        self.isDisabled = False

        """
        The special direct object is used for trigger messages and the like.
        """
        #self.specialDirectObject.accept("ladder_trigger_enter", self.setFly, [True])
        #self.specialDirectObject.accept("ladder_trigger_exit", self.setFly, [False])
        
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])    
        
        # Expose agent's right hand joint to attach objects to
        self.player_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'Hand.R')
        self.player_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'Hand.L')
        
        self.right_hand_holding_object = None
        self.left_hand_holding_object  = None
        
        # don't change the color of things you pick up
        self.player_right_hand.setColorScaleOff()
        self.player_left_hand.setColorScaleOff()
        
        self.player_head  = self.actor.exposeJoint(None, 'modelRoot', 'Head')
        self.neck = self.actor.controlJoint(None, 'modelRoot', 'Head')
        self.neck.setP(bound(self.neck.getP() - 15, -60, 80))
        
        self.controlMap = {"turn_left":0,
                           "turn_right":0,
                           "move_forward":0,
                           "move_backward":0,
                           "move_right":0, 
                           "move_left":0,
                           "look_up":0,
                           "look_down":0,
                           "look_left":0,
                           "look_right":0,
                           "jump":0}
        # see update method for uses, indices are [turn left, turn right, move_forward, move_back, move_right, move_left, look_up, look_down, look_right, look_left]
        # turns are in degrees per second, moves are in units per second
        self.speeds = [270, 270, 5, 5, 5, 5, 60, 60, 60, 60]
      
        # allow for a default position
        if position is not None:
            self.setPosition(position)
        self.originalPos = self.actor.getPos()
        
                
        bubble = loader.loadTexture("media/textures/thought_bubble.png")
        #bubble.setTransparency(TransparencyAttrib.MAlpha)
    
        self.speech_bubble =DirectLabel(parent=self.actor, text="",  text_wordwrap=10, pad=(3,3), relief=None, text_scale=(.6,.6), pos = (0,0,3.6), frameColor=(.6,.2,.1,.5), textMayChange=1, text_frame=(0,0,0,1), text_bg=(1,1,1,1))
        #self.myImage=
        self.speech_bubble.setTransparency(TransparencyAttrib.MAlpha)
        # stop the speech bubble from being colored like the agent
        self.speech_bubble.setColorScaleOff()
        self.speech_bubble.setBin("fixed", 40)
        self.speech_bubble.setDepthTest(False)
        self.speech_bubble.setDepthWrite(False)
        self.speech_bubble.component('text0').textNode.setCardDecal(1)
        self.speech_bubble.setBillboardAxis()
        # hide the speech bubble from IsisAgent's own camera
        self.speech_bubble.hide(BitMask32.bit(1))
        
        
        self.thought_bubble =DirectLabel(parent=self.actor, text="", text_wordwrap=9, text_frame=(1,0,-2,1), text_pos=(0,.5), text_bg=(1,1,1,0), relief=None, frameSize=(0,1.5,-2,3), text_scale=(.18,.18), pos = (0,0.2,3.6), textMayChange=1, image=bubble, image_pos=(0,0.1,0), sortOrder=5)
        self.thought_bubble.setTransparency(TransparencyAttrib.MAlpha)
        # stop the speech bubble from being colored like the agent
        self.thought_bubble.setColorScaleOff()
        self.thought_bubble.component('text0').textNode.setFrameColor(1, 1, 1, 0)
        self.thought_bubble.component('text0').textNode.setFrameAsMargin(0.1, 0.1, 0.1, 0.1)
        self.thought_bubble.component('text0').textNode.setCardDecal(1)
        self.thought_bubble.setBillboardAxis()
        # hide the thought bubble from IsisAgent's own camera
        self.thought_bubble.hide(BitMask32.bit(1))
        # disable by default
        self.thought_bubble.hide()
        self.thought_filter = {}  # only show thoughts whose values are in here
        self.last_spoke = 0 # timers to keep track of last thought/speech and 
        self.last_thought =0 # hide visualizations
        
        # put a camera on ralph
        self.fov = NodePath(Camera('RaphViz'))
        self.fov.node().setCameraMask(BitMask32.bit(1))
        
        # position the camera to be infront of Boxman's face.
        self.fov.reparentTo(self.player_head)
        # x,y,z are not in standard orientation when parented to player-Head
        self.fov.setPos(0, 0.2, 0)
        # if P=0, canrea is looking directly up. 90 is back of head. -90 is on face.
        self.fov.setHpr(0,-90,0)

        lens = self.fov.node().getLens()
        lens.setFov(60) #  degree field of view (expanded from 40)
        lens.setNear(0.2)
        #self.fov.node().showFrustum() # displays a box around his head
        #self.fov.place()
 
        self.prevtime = 0
        self.current_frame_count = 0

        self.isSitting = False
        self.isDisabled = False
        self.actorNodePath.setPythonTag("agent", self)

        # Initialize the action queue, with a maximum length of queueSize
        self.queue = []
        self.queueSize = queueSize
        self.lastSense = 0
        
    def setLayout(self,layout):
        """ Dummy method called by spatial methods for use with objects. 
        Doesn't make sense for an agent that can move around."""
        pass

    def setPos(self,pos):
        """ Wrapper to set the position of the ODE geometry, which in turn 
        sets the visual model's geometry the next time the update() method
        is called. """
        self.setGeomPos(pos)
    
    def setPosition(self,pos):
        self.setPos(pos)
         
    def reparentTo(self, parent):
        self.actorNodePath.reparentTo(parent)

    def _set_control(self, control, value):
        """Set the state of one of the character's movement controls.  """
        self.controlMap[control] = value
   
   
    def get_objects_in_field_of_vision(self,exclude=None):
        """ This works in an x-ray style. Fast. Works best if you listen to
        http://en.wikipedia.org/wiki/Rock_Art_and_the_X-Ray_Style while
        you use it.
       
        needs to exclude isisobjects since they cannot be serialized  
        """
        def compute2dPosition(nodePath, point = Point3(0, 0, 0)): 
            """ Computes a 3-d point, relative to the indicated node, into a 
            2-d point as seen by the camera.  The range of the returned value 
            is based on the len's current film size and film offset, which is 
            (-1 .. 1) by default. 
            
            Code from http://www.panda3d.org/forums/viewtopic.php?t=259
            """ 
            
            # Convert the point into the camera's coordinate space 
            p3d = self.fov.getRelativePoint(nodePath, point) 

            # Ask the lens to project the 3-d point to 2-d. 
            p2d = Point2() 
            #if base.camLens.project(p3d, p2d): 
            if self.fov.node().getLens().project(p3d, p2d): 
                # Got it! 
                return p2d 

            # If project() returns false, it means the point was behind the # lens. 
            return None 
        if exclude == None:
            exclude = ['isisobject', 'all_attributes']
        objects = {}
        # find all objects with 'isisobj' tag.  Doesn't work for Python tags 
        for obj in base.render.findAllMatches("**/=isisobj"):
            o = obj.getPythonTag("isisobj")
            bounds = o.activeModel.getBounds() 
            bounds.xform(o.activeModel.getMat(self.fov))
            if self.fov.node().isInView(o.activeModel.getPos(self.fov)):
                pos = compute2dPosition(o.activeModel, self.fov.getPos(self.fov))
                object_dict = {}
                if 'x_pos' not in exclude: object_dict['x_pos'] = pos[0] 
                if 'y_pos' not in exclude: object_dict['y_pos'] = pos[1] 
                if 'distance' not in exclude: object_dict['distance'] = o.activeModel.getDistance(self.fov)
                if 'orientation' not in exclude: object_dict['orientation'] = o.activeModel.getH(self.fov)
                if 'actions' not in exclude: object_dict['actions'] = o.get_all_action_names()
                if 'all_attributes' not in exclude: 
                    object_dict['attributes'] = o.get_all_attributes_and_values(False)
                else:
                    # shows only attributes that have visible=True.
                    object_dict['attributes'] = o.get_all_attributes_and_values(True)
                if 'isisobject' not in exclude: object_dict['isisobject'] = o
                if 'class' not in exclude: object_dict['class'] = o.get_class_name()
                if object_dict['x_pos']>= -1 and object_dict['x_pos']<= 1: 
                # add item to dictionary
                    objects[o] = object_dict
        return objects
    
    def get_objects_spatial_relations(self):
        seen = []
        spatial_relations = []
        for node in base.render.findAllMatches("**/=isisobj"):
            node = node.getPythonTag("isisobj")
            if hasattr(node,'in_layout'):
                for item in node.in_layout.items:
                    item = item.getPythonTag("isisobj")
                    spatial_relations.append(('in', node.name, item.name))
            if hasattr(node,'on_layout'):
                for item in node.on_layout.items:
                    item = item.getPythonTag("isisobj")
                    spatial_relations.append(('on', node.name, item.name))
        return spatial_relations
    
    def get_class_name(self):
        return self.__class__.__name__

    def get_agents_in_field_of_vision(self):
        """ This works in an x-ray vision style as well"""
        agents = {}
        for agent in base.render.findAllMatches("**/agent-*"):
            if not agent.hasPythonTag("agent"):
                continue
            a = agent.getPythonTag("agent")
            bounds = a.actorNodePath.getBounds()
            bounds.xform(a.actorNodePath.getMat(self.fov))
            pos = a.actorNodePath.getPos(self.fov)
            if a == self or self.fov.node().isInView(pos):
                p1 = self.fov.getRelativePoint(render,pos)
                p2 = Point2()
                self.fov.node().getLens().project(p1, p2)
                p3 = aspect2d.getRelativePoint(render2d, Point3(p2[0], 0, p2[1]))
                agentDict = {'x_pos': p3[0],\
                             'y_pos': p3[2],\
                             'distance':a.actorNodePath.getDistance(self.fov),\
                             'orientation': a.actorNodePath.getH(self.fov),\
                             'class': a.get_class_name()}
                agents[a] = agentDict
        return agents
    
    def in_view(self,isisobj):
        """ Returns true iff a particular isisobject is in view """
        return len(filter(lambda x: x['isisobject'] == isisobj, self.get_objects_in_field_of_vision(exclude=[]).values()))

    def get_objects_in_view(self):
        """ Gets objects through ray tracing.  Slow"""
        return self.picker.get_objects_in_view()
    
    
    # capture retina image functions
    
    def initialize_retina(self):
        fbp=FrameBufferProperties(FrameBufferProperties.getDefault())
        self.retina_buffer = base.win.makeTextureBuffer("retina-buffer-%s" % (self.name), 320, 240, tex=Texture('retina-texture'), to_ram=True, fbp=fbp)
        self.retina_buffer.setActive(False)
        #self.retina_buffer.setOneShot(True)
        self.retina_texture = Texture("retina-texture-%s" % (self.name))
        self.retina_buffer.addRenderTexture(self.retina_texture, GraphicsOutput.RTMCopyRam)
        self.retina_buffer.setSort(-100)
        self.retina_camera = base.makeCamera(self.retina_buffer)
        self.retina_camera.node().getLens().setFov(60)
        self.retina_camera.node().getLens().setNear(0.2)
        self.retina_camera.node().setCameraMask(BitMask32.bit(1))
        self.retina_camera.reparentTo(self.player_head)
        self.retina_camera.setPos(0, 0.2, 0)
        self.retina_camera.setHpr(0,-90,0)
        print "initialized agent Texture Buffer"
        
    def capture_retina_rgb_ram_image(self):
        self.retina_buffer.setActive(True)
        base.graphicsEngine.renderFrame()
        ram_image_data = self.retina_texture.getRamImageAs('RGB')
        self.retina_buffer.setActive(False)
        if (not ram_image_data) or (ram_image_data is None):
            print 'Failed to get ram image from retina texture.'
            return None
        rgb_ram_image = {'dict_type':'rgb_ram_image', 'width':self.retina_texture.getXSize(), 'height':self.retina_texture.getYSize(), 'rgb_data':ram_image_data}
        return rgb_ram_image
    
    def capture_retina_xmlrpc_image(self):
        rgb_ram_image = self.capture_retina_rgb_ram_image()
        if rgb_ram_image is None:
            return None
        return rgb_ram_image__as__xmlrpc_image(rgb_ram_image)
    
    # control functions
    
    def control__turn_left__start(self, speed=None):
        self._set_control("turn_left",  1)
        self._set_control("turn_right", 0)
        if speed:
            self.speeds[0] = speed
        return "success"

    def control__turn_left__stop(self):
        self._set_control("turn_left",  0)
        return "success"

    def control__turn_right__start(self, speed=None):
        self._set_control("turn_left",  0)
        self._set_control("turn_right", 1)
        if speed:
            self.speeds[1] = speed
        return "success"

    def control__turn_right__stop(self):
        self._set_control("turn_right", 0)
        return "success"

    def control__move_forward__start(self, speed=None):
        self._set_control("move_forward",  1)
        self._set_control("move_backward", 0)
        if speed:
            self.speeds[2] = speed
        return "success"

    def control__move_forward__stop(self):
        self._set_control("move_forward",  0)
        return "success"

    def control__move_backward__start(self, speed=None):
        self._set_control("move_forward",  0)
        self._set_control("move_backward", 1)
        if speed:
            self.speeds[3] = speed
        return "success"

    def control__move_backward__stop(self):
        self._set_control("move_backward", 0)
        return "success"

    def control__move_left__start(self, speed=None):
        self._set_control("move_left",  1)
        self._set_control("move_right", 0)
        if speed:
            self.speeds[4] = speed
        return "success"

    def control__move_left__stop(self):
        self._set_control("move_left",  0)
        return "success"

    def control__move_right__start(self, speed=None):
        self._set_control("move_right",  1)
        self._set_control("move_left", 0)
        if speed:
            self.speeds[5] = speed
        return "success"

    def control__move_right__stop(self):
        self._set_control("move_right",  0)
        return "success"

    def control__look_left__start(self, speed=None):
        self._set_control("look_left",  1)
        self._set_control("look_right", 0)
        if speed:
            self.speeds[9] = speed
        return "success"

    def control__look_left__stop(self):
        self._set_control("look_left",  0)
        return "success"

    def control__look_right__start(self, speed=None):
        self._set_control("look_right",  1)
        self._set_control("look_left", 0)
        if speed:
            self.speeds[8] = speed
        return "success"

    def control__look_right__stop(self):
        self._set_control("look_right",  0)
        return "success"

    def control__look_up__start(self, speed=None):
        self._set_control("look_up",  1)
        self._set_control("look_down", 0)
        if speed:
            self.speeds[6] = speed
        return "success"

    def control__look_up__stop(self):
        self._set_control("look_up",  0)
        return "success"

    def control__look_down__start(self, speed=None):
        self._set_control("look_down",  1)
        self._set_control("look_up",  0)
        if speed:
            self.speeds[7] = speed
        return "success"

    def control__look_down__stop(self):
        self._set_control("look_down",  0)
        return "success"

    def control__jump(self):
        self._set_control("jump",  1)
        return "success"

    def control__view_objects(self):
        """ calls a raytrace to to all objects in view """
        objects = self.get_objects_in_field_of_vision()
        self.control__say("If I were wearing x-ray glasses, I could see %i items"  % len(objects)) 
        print "Objects in view:", objects
        return objects

    def control__sense(self):
        """ perceives the world, returns percepts dict """
        percepts = dict()
        # eyes: visual matricies
        #percepts['vision'] = self.sense__get_vision()
        # objects in purview (cheating object recognition)
        percepts['objects'] = self.sense__get_objects()
        # global position in environment - our robots can have GPS :)
        percepts['position'] = self.sense__get_position()
        # language: get last utterances that were typed
        percepts['language'] = self.sense__get_utterances()
        # agents: returns a map of agents to a list of actions that have been sensed
        percepts['agents'] = self.sense__get_agents()
        # spatial relations
        sr = self.get_objects_spatial_relations()
       
        # filter spatial relations based on what is in the object key 
        filter_non_objects = lambda x: percepts['objects'].has_key(x[1]) and percepts['objects'].has_key(x[2])
        percepts['spatial_relations'] =  filter(filter_non_objects, sr)
        
        print percepts
        return percepts
    
    def control__sense_retina_image(self):
        return self.capture_retina_xmlrpc_image()
    
    def control__think(self, message, layer=0):
        """ Changes the contents of an agent's thought bubble"""
        # only say things that are checked in the controller
        if self.thought_filter.has_key(layer):
            self.thought_bubble.show()
            self.thought_bubble['text'] = message
            #self.thought_bubble.component('text0').textNode.setShadow(0.05, 0.05)
            #self.thought_bubble.component('text0').textNode.setShadowColor(self.thought_filter[layer])
            self.last_thought = 0
        return "success"

    def control__say(self, message = "Hello!"):
        self.speech_bubble['text'] = message
        self.last_spoke = 0
        return "success"
    
    """

    Methods explicitly for IsisScenario files 

    """

    def put_in_front_of(self,isisobj):
        # find open direction
        pos = isisobj.getGeomPos()
        direction = render.getRelativeVector(isisobj, Vec3(0, 1.0, 0))
        closestEntry, closestObject = IsisAgent.physics.doRaycastNew('aimRay', 5, [pos, direction], [isisobj.geom])   
        print "CLOSEST",closestEntry, closestObject
        if closestObject == None:
            self.setPosition(pos + Vec3(0,2,0))
        else:
            print "CANNOT PLACE IN FRONT OF %s BECAUSE %s IS THERE" % (isisobj,closestObject)
            direction = render.getRelativeVector(isisobj, Vec3(0, -1.0, 0))
            closestEntry, closestObject = IsisAgent.physics.doRaycastNew('aimRay', 5, [pos, direction], [isisobj.geom])     
            if closestEntry == None:
                self.setPosition(pos + Vec3(0,-2,0))
            else:
                print "CANNOT PLACE BEHIND %s BECAUSE %s IS THERE" % (isisobj,closestObject)
                direction = render.getRelativeVector(isisobj, Vec3(1, 0, 0))
                closestEntry, closestObject = IsisAgent.physics.doRaycastNew('aimRay', 5, [pos, direction], [isisobj.geom])    
                if closestEntry == None:
                    self.setPosition(pos + Vec3(2,0,0))
                else:
                    print "CANNOT PLACE TO LEFT OF %s BECAUSE %s IS THERE" % (isisobj,closestObject)
                    # there's only one option left, do it anyway
                    self.setPosition(pos + Vec3(-2,0,0))
        # rotate agent to look at it
        self.actorNodePath.setPos(self.getGeomPos())
        self.actorNodePath.lookAt(pos)
        self.setH(self.actorNodePath.getH())
        
    def put_in_right_hand(self,target):
        return self.pick_object_up_with(target, self.right_hand_holding_object, self.player_right_hand)
                    
    def put_in_left_hand(self,target):
        return self.pick_object_up_with(target, self.left_hand_holding_object, self.player_left_hand)

    def __get_object_in_center_of_view(self):
       direction = render.getRelativeVector(self.fov, Vec3(0, 1.0, 0))
       pos = self.fov.getPos(render)
       exclude = []#[base.render.find("**/kitchenNode*").getPythonTag("isisobj").geom]
       closestEntry, closestObject = IsisAgent.physics.doRaycastNew('aimRay', 5, [pos, direction], exclude)
       return closestObject
    
    def pick_object_up_with(self,picked_up,hand_slot,hand_joint):
        """ Attaches an IsisObject, picked_up, to the hand joint.  Does not check anything first,
        other than the fact that the hand joint is not currently holding something else."""
        if hand_slot != None:
            print 'already holding ' + hand_slot.getName() + '.'
            return None  
        else:
            if picked_up.layout:
                if picked_up.layout.parent.has_attribute('is_open') and not picked_up.layout.parent.get_attribute_value('is_open'):
                    print "Error: %s is part of a closed container." % (picked_up)
                    return "error: cannot remove item from closed container"
                picked_up.layout.remove(picked_up)
                picked_up.layout = None
            # store original position
            picked_up.originalHpr = picked_up.getHpr(render)
            picked_up.disable() #turn off physics
            if picked_up.body: picked_up.body.setGravityMode(0)
            picked_up.reparentTo(hand_joint)
            # TODO: if object is a surface
            #  - perturb its contained objects to turn physics back on
            #  if object is a container
            #  - turn off the physics of the contained objects, 
            #   so that they move with the object
            picked_up.setFluidPosition(hand_joint.getPos(render) + Vec3(*picked_up.pickup_vector[0:3]))
            picked_up.setRotation(Vec3(*picked_up.pickup_vector[3:]))
            picked_up.setTag('heldBy', self.name)
            if hand_joint == self.player_right_hand:
                self.right_hand_holding_object = picked_up
            elif hand_joint == self.player_left_hand:
                self.left_hand_holding_object = picked_up
            hand_slot = picked_up # does this do anything?
            return picked_up

    def control__pick_up_with_right_hand(self, target=None):
        """ Tries to find an object with 'target' as a substring of its name that is:
        
          1. has the isisobj tag, which points to the IsisWorld generator Python object
          2. is part of an IsisObject node
          3. has the pickable tag, indicating it can be picked up
          4. is within reach, meaning self.can_grasp(item) == True
        
        If it fails, it returns an error string specifying which type of error occurred.
        Alternatively, if target=None, then it is populated with whatever item is in the center
        of the agent's field of view.  This was originally used for the key-binding pick up 
        commands.
        
        This command is almost identicial for the left/right hands, changes in one
        should correspond with changes in the other.
        """
        if not target:
            found_item = self.__get_object_in_center_of_view()
            if not target:
                print "no target in reach"
                return "error: no target in center of view"
        else:
            found_items = IsisAgent.physics.main.worldNode.findAllMatches("**/%s*" % (target))
            if not found_items:
                print "no target name %s found" % (target)
                return "error: no target by that name"
            found_item = None
            for potential_item in found_items:
                if potential_item.hasPythonTag('isisobj'):
                    found_item = potential_item.getPythonTag("isisobj")
                    break
            if not found_item:
                print "targets matching %s were not isisobj and pickable" % (target)
                return "error: no pickable isisobjects by name %s" % (target)
        print "attempting to pick up " + found_item.name + " with right hand.\n"
        if self.can_grasp(found_item): # object within distance      
            picked_up = self.pick_object_up_with(found_item, self.right_hand_holding_object, self.player_right_hand)
            if picked_up != None:
                return 'success'
            else:
                return 'failure'
        else:
            print 'object (' + found_item.name + ') is not graspable (i.e. in view and close enough).'
            return 'error: object not graspable'

    def control__pick_up_with_left_hand(self, target=None):
        """ Tries to find an object with 'target' as a substring of its name that is:
        
          1. has the isisobj tag, which points to the IsisWorld generator Python object
          2. is part of an IsisObject node
          3. has the pickable tag, indicating it can be picked up
          4. is within reach, meaning self.can_grasp(item) == True
        
        If it fails, it returns an error string specifying which type of error occurred.
        
        Alternatively, if target=None, then it is populated with whatever item is in the center
        of the agent's field of view.  This was originally used for the key-binding pick up 
        commands.
        
        This command is almost identicial for the left/right hands, changes in one
        should correspond with changes in the other.
        """
        if not target:
            found_item = self.__get_object_in_center_of_view()
            if not target:
                print "no target in reach"
                return "error: no target in center of view"
        else:
            found_items = IsisAgent.physics.main.worldNode.findAllMatches("**/%s*" % (target))
            if not found_items:
                print "no target name %s found" % (target)
                return "error: no target by that name"
            found_item = None
            for potential_item in found_items:
                print "potential -item",potential_item, potential_item.hasPythonTag('pickable'),potential_item.hasPythonTag('isisobj')
                if potential_item.hasPythonTag('isisobj'):
                    found_item = potential_item.getPythonTag("isisobj")
                    break
            if not found_item:
                print "targets matching %s were not isisobj and pickable" % (target)
                return "error: no pickable isisobjects by name %s" % (target)
        print "attempting to pick up " + found_item.name + " with left hand.\n"
        if self.can_grasp(found_item): # object within distance      
            picked_up = self.pick_object_up_with(found_item, self.left_hand_holding_object, self.player_left_hand)
            if picked_up != None:
                return 'success'
            else:
                return 'failure'
        else:
            print 'object (' + found_item.name + ') is not graspable (i.e. in view and close enough).'
            return 'error: object not graspable'   


    def control__drop_from_right_hand(self, throw_object=True):
        print "attempting to drop object from right hand.\n"
        
        if self.right_hand_holding_object is None:
            print 'right hand is not holding an object.'
            return False
        if self.right_hand_holding_object.getNetTag('heldBy') == self.name:
            self.right_hand_holding_object.reparentTo(render)
            direction = render.getRelativeVector(self.fov, Vec3(1.0, 0, 0))
            pos = self.player_right_hand.getPos(render)
            heldPos = self.right_hand_holding_object.geom.getPosition()
            #self.right_hand_holding_object.setPosition(pos)
            #self.right_hand_holding_object.synchPosQuatToNode()
            self.right_hand_holding_object.setTag('heldBy', '')
            #self.right_hand_holding_object.setRotation(self.right_hand_holding_object.originalHpr)
            self.right_hand_holding_object.enable()

            if self.right_hand_holding_object.body:
                quat = self.getQuat()
                # throw object
                force = 5
                self.right_hand_holding_object.body.setGravityMode(1)
                self.right_hand_holding_object.getBody().setForce(quat.xform(Vec3(0, 0, -1)))
            self.right_hand_holding_object = None
            return 'success'
        else:
            return "Error: not being held by agent %s" % (self.name)

    
    def control__drop_from_left_hand(self, throw_object=True):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is None:
            return 'left hand is not holding an object.'
        if self.left_hand_holding_object.getNetTag('heldBy') == self.name:
            self.left_hand_holding_object.reparentTo(render)
            direction = render.getRelativeVector(self.fov, Vec3(1.0, 0, 0))
            pos = self.player_left_hand.getPos(render)
            #heldPos = self.left_hand_holding_object.geom.getPosition()
            #self.left_hand_holding_object.setPosition(pos)
            #self.left_hand_holding_object.synchPosQuatToNode()
            self.left_hand_holding_object.setTag('heldBy', '')
            #self.left_hand_holding_object.setRotation(self.left_hand_holding_object.originalHpr)
            self.left_hand_holding_object.enable()
            if self.left_hand_holding_object.body:# and throw_object:
                quat = self.getQuat()
                # throw object
                force = -1
                self.left_hand_holding_object.body.setGravityMode(1)
                self.left_hand_holding_object.getBody().setForce(quat.xform(Vec3(0,0, force)))
            self.left_hand_holding_object = None
            return 'success'
        else:
            return "Error: not being held by agent %s" % (self.name)


    def control__use_right_hand(self, target = None, action = None):
        # TODO, rename this to use object with 
        if not action:
            return "error: no action specified in IsisAgent::control__use_right_hand "
        if not target:
            found_item = self.__get_object_in_center_of_view()
            if not found_item:
                print "no target in reach"
                return
        else:
            found_items = IsisAgent.physics.main.worldNode.findAllMatches("**/%s*" % (target))
            if not found_items:
                print "no target name %s found" % (target)
                return "error: no target by that name"
            found_item = None
            for potential_item in found_items:
                if potential_item.hasPythonTag('isisobj'):
                    found_item = potential_item.getPythonTag("isisobj")
                    break
            if not found_item:
                print "No suitable isisobject found"
                return "no suitable isisobject found"
        print "Trying to use object", found_item
        if self.can_grasp(found_item):
            if(found_item.call(self, action, self.right_hand_holding_object) or
              (self.right_hand_holding_object and self.right_hand_holding_object.call(self, action, found_item))):
                return "success"
            return str(action) + " not associated with either target or object"
        return "target not within reach"

    def control__use_left_hand(self, target = None, action = None):
        if not action:
            return "error: no action specified in IsisAgent::control__use_right_hand "
        if not target:
            found_item = self.__get_object_in_center_of_view()
            if not found_item:
                print "no target in reach"
                return
        else:
            found_items = IsisAgent.physics.main.worldNode.findAllMatches("**/%s*" % (target))
            if not found_items:
                print "no target name %s found" % (target)
                return "error: no target by that name"
            found_item = None
            for potential_item in found_items:
                if potential_item.hasPythonTag('isisobj'):
                    found_item = potential_item.getPythonTag("isisobj")
                    break
            if not found_item:
                print "No suitable isisobject found"
                return "no suitable isisobject found"
        print "Trying to use object", found_item
        if self.can_grasp(found_item):
            if(found_item.call(self, action, self.left_hand_holding_object) or
              (self.left_hand_holding_object and self.left_hand_holding_object.call(self, action, found_item))):
                return "success"
            return str(action) + " not associated with either target or object"
        return "target not within reach"

    def can_grasp(self, isisobject):
        distance = isisobject.activeModel.getDistance(self.fov)
        print "distance = ", distance
        return distance < 5.0

    def is_holding(self, object_name):
        return ((self.left_hand_holding_object and (self.left_hand_holding_object.getPythonTag('isisobj').name  == object_name)) \
             or (self.right_hand_holding_object and (self.right_hand_holding_object.getPythonTag('isisobj').name == object_name)))

    def empty_hand(self):
        if (self.left_hand_holding_object is None):
            return self.player_left_hand
        elif (self.right_hand_holding_object is None):
            return self.player_right_hand
        return False

    def has_empty_hand(self):
        return (self.empty_hand() is not False)

    def control__use_aimed(self):
        """
        Try to use the object that we aim at, by calling its callback method.
        """
        target = self.__get_object_in_center_of_view()
	if not target:
	    print "No target in FOV"
            return "failure"
        if target.selectionCallback:
            target.selectionCallback(self, dir)
        return "success"
                    

    def sense__get_position(self):
        x,y,z = self.actorNodePath.getPos()
        h,p,r = self.actorNodePath.getHpr()
        #FIXME
        # neck is not positioned in Blockman nh,np,nr = self.agents[agent_id].actor_neck.getHpr()
        left_hand_obj = "" 
        right_hand_obj = "" 
        if self.left_hand_holding_object:  
            left_hand_obj = {self.left_hand_holding_object.getName() : self.left_hand_holding_object.get_all_attributes_and_values(False)}
        if self.right_hand_holding_object: 
            right_hand_obj = {self.right_hand_holding_object.getName() : self.right_hand_holding_object.get_all_attributes_and_values(False)}
        return {'body_pos' : list(self.actorNodePath.getPos())+list(self.actorNodePath.getHpr()),
                'left_hand_pos': list(self.player_left_hand.getPos())+list(self.player_left_hand.getHpr()),
                'right_hand_pos': list(self.player_right_hand.getPos())+list(self.player_right_hand.getHpr()),
                'neck_pos': list(self.neck.getPos())+list(self.neck.getHpr()),
                'in_left_hand':left_hand_obj,
                'in_right_hand':right_hand_obj}

    def sense__get_vision(self):
        self.fov.node().saveScreenshot("temp.jpg")
        image = Image.open("temp.jpg")
        os.remove("temp.jpg")
        return image

    def sense__get_objects(self):
        return dict([x.getName(),y] for (x,y) in self.get_objects_in_field_of_vision().items())

    def sense__get_agents(self):
        curSense = self.physics.main.get_current_physics_time()
        agents = {}
        for k, v in self.get_agents_in_field_of_vision().items():
            v['actions'] = k.get_other_agents_actions(self.lastSense, curSense)
            agents[k.name] = v
        self.lastSense = curSense
        return agents

    def sense__get_utterances(self):
        """ Clear out the buffer of things that the teacher has typed,
        FIXME: this doesn't work right now """
        return []
        utterances = self.teacher_utterances
        self.teacher_utterances = []
        return utterances

    def debug__print_objects(self):
        text = "Objects in FOV: "+ ", ".join(self.sense__get_objects().keys())
        print text

    def add_action_to_history(self, action, args, result = 0):
        self.queue.append({'time':self.physics.main.get_current_physics_time(), 'action':action, 'args':args, 'result':result})
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)

    def get_other_agents_actions(self, start = 0, end = None):
        if not end:
            end = self.physics.main.get_current_physics_time()
        actions = []
        for act in self.queue:
            if act['time'] >= start:
                if act['time'] < end:
                    actions.append(act)
                else:
                    break
        return actions



    def update(self, stepSize=0.1):
        
        self.speed = [0.0, 0.0]
        self.actorNodePath.setPos(self.geom.getPosition()+Vec3(0,0,-0.70))
        self.actorNodePath.setQuat(self.getQuat())
        # the values in self.speeds are used as coefficientes for turns and movements
        if (self.controlMap["turn_left"]!=0):        self.addToH(stepSize*self.speeds[0])
        if (self.controlMap["turn_right"]!=0):       self.addToH(-stepSize*self.speeds[1])
        if self.verticalState == 'ground':
            # these actions require contact with the ground
            if (self.controlMap["move_forward"]!=0):     self.speed[1] =  self.speeds[2]
            if (self.controlMap["move_backward"]!=0):    self.speed[1] = -self.speeds[3]
            if (self.controlMap["move_left"]!=0):        self.speed[0] = -self.speeds[4]
            if (self.controlMap["move_right"]!=0):       self.speed[0] =  self.speeds[5]
            if (self.controlMap["jump"]!=0):             
                kinematicCharacterController.jump(self)
                # one jump at a time!
                self.controlMap["jump"] = 0
        if (self.controlMap["look_left"]!=0):        self.neck.setR(bound(self.neck.getR(),-180,180)+stepSize*self.speeds[9])
        if (self.controlMap["look_right"]!=0):       self.neck.setR(bound(self.neck.getR(),-180,180)-stepSize*self.speeds[8])
        if (self.controlMap["look_up"]!=0):
            self.neck.setP(bound(self.neck.getP(),-60,80)+stepSize*self.speeds[6])
        if (self.controlMap["look_down"]!=0):
            self.neck.setP(bound(self.neck.getP(),-60,80)-stepSize*self.speeds[7])

        kinematicCharacterController.update(self, stepSize)

        """
        Update the held object position to be in the hands
        """
        if self.right_hand_holding_object != None:
            self.right_hand_holding_object.setPosition(self.player_right_hand.getPos(render)+Vec3(*self.right_hand_holding_object.pickup_vector[0:3]))
        if self.left_hand_holding_object != None:
            self.left_hand_holding_object.setPosition(self.player_left_hand.getPos(render)+Vec3(*self.left_hand_holding_object.pickup_vector[0:3]))

        #Update the dialog box and thought windows
        #This allows dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += stepSize/2
        self.last_thought += stepSize/2
        self.speech_bubble['text_bg']=(1,1,1,1/(self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(self.last_spoke+0.01))
        if self.last_spoke > 2:
            self.speech_bubble['text'] = ""
        if self.last_thought > 1:
            self.thought_bubble.hide()

        # If the character is moving, loop the run animation.
        # If he is standing still, stop the animation.
        if (self.controlMap["move_forward"]!=0) or (self.controlMap["move_backward"]!=0) or (self.controlMap["move_left"]!=0) or (self.controlMap["move_right"]!=0):
            if self.isMoving is False:
                self.isMoving = True
        else:
            if self.isMoving:
                self.current_frame_count = 5.0
                self.isMoving = False

        total_frame_num = self.actor.getNumFrames('walk')
        if self.isMoving:
            self.current_frame_count = self.current_frame_count + (stepSize*250.0)
            if self.current_frame_count > total_frame_num:
                self.current_frame_count = self.current_frame_count%total_frame_num
            self.actor.pose('walk', self.current_frame_count)
        elif self.current_frame_count != 0:
            self.current_frame_count = 0
            self.actor.pose('idle', 0)
        return Task.cont
        
    def destroy(self):
        self.disable()
        self.specialDirectObject.ignoreAll()
        self.actorNodePath.removeNode()
        del self.specialDirectObject
        kinematicCharacterController.destroy(self)

    def disable(self):
        self.isDisabled = True
        self.geom.disable()
        self.footRay.disable()

    def enable(self):
        self.footRay.enable()
        self.geom.enable()
        self.isDisabled = False
    """
    Set camera to correct height above the center of the capsule
    when crouching and when standing up.
    """
    def crouch(self):
        kinematicCharacterController.crouch(self)
        self.camH = self.crouchCamH

    def crouchStop(self):
        """
        Only change the camera's placement when the KCC allows standing up.
        See the KCC to find out why it might not allow it.
        """
        if kinematicCharacterController.crouchStop(self):
            self.camH = self.walkCamH




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


