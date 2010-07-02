import direct.directbase.DirectStart 
from direct.showbase.DirectObject import DirectObject 
from direct.actor.Actor import Actor 
from direct.task import Task 

from direct.controls.ControlManager import CollisionHandlerRayStart
from pandac.PandaModules import CollisionTraverser 
from pandac.PandaModules import ActorNode

from direct.showbase import DirectObject
from direct.interval.IntervalGlobal import *
from direct.actor.Actor import Actor
from direct.gui.DirectGui import DirectLabel
from direct.controls.GravityWalker import GravityWalker
from pandac.PandaModules import *# PandaNode,NodePath,Camera
#from panda3d.core import CollisionHandlerPusher, CollisionHandlerGravity, CollisionTraverser
import math, random
# project stuff
from ..actions.actions import *

def frange(x,y,inc):
    """ Floating point xrange """
    while x <= y:
        if x < 0:
            yield -(abs(x)**2)
        else:
            yield x**2
        x += inc


class Ralph(DirectObject.DirectObject):
    notify = directNotify.newCategory("GravityWalker")
    wantDebugIndicator = base.config.GetBool('want-avatar-physics-indicator', 0)
    wantFloorSphere = base.config.GetBool('want-floor-sphere', 0)
    earlyEventSphere = base.config.GetBool('early-event-sphere', 0)

    DiagonalFactor = math.sqrt(2.) / 2.
    def __init__(self, worldManager, agentSimulator, name, worldObjectsDict, queueSize = 100):

        # setup the visual aspects of ralph
        self.actor= Actor("models/boxman",{"walk":"models/boxman-walk", "idle": "models/boxman-idle"})
        self.actor.setScale(1.0)
        self.actor.setH(0)
        self.actor.setColorScale(random.random(), random.random(), random.random(), 1.0)
        self.actorNode = ActorNode('physicsControler-%s' % name)
        self.actorNodePath = render.attachNewNode(self.actorNode)
        self.actor.reparentTo(self.actorNodePath)
        self.name = name
        DirectObject.DirectObject.__init__(self)
        #self.walker.cWallSphereNodePath.setCollideMask(BitMask32().bit(3))      
        self.agent_simulator = agentSimulator
        self.worldManager = worldManager    
        



        self.__gravity=64.34
        self.__standableGround=3
        self.__hardLandingForce=16
        self._legacyLifter = False

        self.mayJump = 1
        self.jumpDelayTask = None

        self.controlsTask = None
        self.indicatorTask = None

        self.falling = 0
        self.needToDeltaPos = 0
        self.physVelocityIndicator=None
        self.avatarControlForwardSpeed=0
        self.avatarControlJumpForce=0
        self.avatarControlReverseSpeed=0
        self.avatarControlRotateSpeed=0
        self.getAirborneHeight=None

        self.priorParent=Vec3(0)
        self.__oldPosDelta=Vec3(0)
        self.__oldDt=0

        self.moving=0
        self.speed=0.0
        self.rotationSpeed=0.0
        self.slideSpeed=0.0
        self.vel=Vec3(0.0)
        self.collisionsActive = 0

        self.isAirborne = 0
        self.highMark = 0
    
        # walker methods
        self.setAvatar( self.actor ) 
        self.setWalkSpeed( -10, 30, -6, 90 ) 
        self.setWallBitMask( BitMask32.bit(2) ) 
        self.setFloorBitMask( BitMask32.bit(5) ) 
        self.initializeCollisions( base.cTrav, self.actor ) 
        self.placeOnFloor( )
        self.cWallSphereNodePath.setCollideMask(BitMask32().bit(3))
    
    
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])    

        
        # Expose agent's right hand joint to attach objects to
        self.player_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'Hand.R')
        self.player_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'Hand.L')
        self.player_head  = self.actor.exposeJoint(None, 'modelRoot', 'Head')
        self.player_neck = self.actor.controlJoint(None, 'modelRoot', 'Head')
        base.taskMgr.add( self.update, 'update' ) 
             


        
        self.controlMap = {"turn_left":0, "turn_right":0, "move_forward":0, "move_backward":0, "move_right":0, "move_left":0,\
                           "look_up":0, "look_down":0, "look_left":0, "look_right":0, "jump":0}

        self.originalPos = self.actor.getPos()

        # ray for pointing at things
        self.aimRay = None
        self.aimed = None

    
        self.right_hand_holding_object = False
        self.left_hand_holding_object  = False

        # speech bubble
        self.last_spoke = 0
        self.speech_bubble=DirectLabel(parent=self.actor, text="", text_wordwrap=10, pad=(3,3),\
                       relief=None, text_scale=(.3,.3), pos = (0,0,3.6), frameColor=(.6,.2,.1,.5),\
                       textMayChange=1, text_frame=(0,0,0,1), text_bg=(1,1,1,1))
        self.speech_bubble.component('text0').textNode.setCardDecal(1)
        self.speech_bubble.setBillboardAxis()
        
        # put a camera on ralph
        self.fov = NodePath(Camera('RaphViz'))
        
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
        self.isMoving = False

        self.current_frame_count = 0

        #self.name = "Ralph"
        self.isSitting = False
        self.isDisabled = False

        """
        Object used for picking objects in the field of view
        """
        self.picker =None# Picker(self.fov, worldObjectsDict)

        # Initialize the action queue, with a maximum length of queueSize
        self.queue = []
        self.queueSize = queueSize


    def setControl(self, control, value):
        """Set the state of one of the character's movement controls.  """
        self.controlMap[control] = value

    def get_objects(self):
        """ Looks up all of the model nodes that are 'isInView' of the camera"""

        def project_carelessly(lens, point): 
           ''' Similar to Lens.project(), but never returns None-- returning
           inverted image when object is BEHIND camera
           
           code from https://www.panda3d.org/phpbb2/viewtopic.php?p=20245 ''' 

           projection_mat = lens.getProjectionMat() 
           full = projection_mat.xform( VBase4(point[0], point[1], point[2], 1.0) ) 
           if full[3] == 0.0: 
              # There is no meaningful projection for the nodal point of the lens. 
              # So return a value that is Very Far Away. 
              return (1000000.0, 1000000.0, -1000000.0) 

           recip_full3 = 1.0 / full[3] 
           return (full[0] * recip_full3, 
                   full[1] * recip_full3, 
                   full[2] * recip_full3) 

        def map3dToAspect2d(node, point): 
           """Maps the indicated 3-d point (a Point3), which is relative to 
              the indicated NodePath, to the corresponding point in the aspect2d 
              scene graph. Returns the corresponding Point3 in aspect2d. 
              Returns None if the point is not onscreen. """ 

           # Convert the point to the 3-d space of the camera 
           p3 = self.fov.getRelativePoint(node, point) 

           # Convert from camera 3d space to camera 2d space. 
           # Manual override. 
           p2 = project_carelessly(self.fov.node().getLens(), p3) 

           r2d = Point3(p2[0], 0, p2[1]) 

           # And then convert it to aspect2d coordinates 
           a2d = aspect2d.getRelativePoint(render2d, r2d) 

           return a2d

        objs = render.findAllMatches("**/+ModelNode")
        in_view = {}
        for o in objs:
            #o.hideBounds() # in case previously turned on
            o_pos = o.getPos(self.fov)
            if self.fov.node().isInView(o_pos):
                if True:#self.agent_simulator.world_objects.has_key(o.getName()):
                    b_min, b_max =  o.getTightBounds()
                    a_min = map3dToAspect2d(render, b_min)
                    a_max = map3dToAspect2d(render, b_max)
                    if a_min == None or a_max == None:
                        continue
                    #o.showBounds()
                    x_diff = math.fabs(a_max[0]-a_min[0])
                    y_diff = math.fabs(a_max[2]-a_min[2])
                    area = 100*x_diff*y_diff  # percentage of screen
                    object_dict = {'x_pos': (a_min[2]+a_max[2])/2.0,\
                                   'y_pos': (a_min[0]+a_max[0])/2.0,\
                                   'distance':o.getDistance(self.fov), \
                                   'area':area,\
                                   'orientation': o.getH(self.fov)}
                    in_view[o.getName()]=object_dict
#                    print o.getName(), object_dict
#                    print o.getAncestor(1).getName()
#                    print o.getAncestor(1).listTags()
#                    print self.player_neck.getH()
##                    if (o.getAncestor(1).getName() == "Ralph"):
##                       for agent in self.agent_simulator.agents:
##                           if agent.

        self.control__say("I see: "+' and '.join(in_view.keys())) 
        return in_view

    def raytrace_getAllObjectsInView(self):
        return self.picker.getObjectsInView()
            
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

    def control__move_left__start(self):
        self.setControl("move_left",  1)
        self.setControl("move_right", 0)

    def control__move_left__stop(self):
        self.setControl("move_left",  0)

    def control__move_right__start(self):
        self.setControl("move_right",  1)
        self.setControl("move_left", 0)

    def control__move_right__stop(self):
        self.setControl("move_right",  0)

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

    def control__jump(self):
         PhysicsCharacterController.jump(self)

    def control__view_objects(self):
        """ calls a raytrace to to all objects in view """
        objects = self.raytrace_getAllObjectsInView()
        print "Objects in view:", objects
        return objects

    def control__sense(self):
        """ perceives the world, returns percepts dict """
        percepts = dict()
        # eyes: visual matricies
        percepts['vision'] = self.sense__get_vision()
        # objects in purview (cheating object recognition)
        percepts['objects'] = self.sense__get_objects()
        # global position in environment - our robots can have GPS :)
        percepts['position'] = self.sense__get_position()
        # language: get last utterances that were typed
        percepts['language'] = self.sense__get_utterances()
        return percepts
 
    def can_grasp(self, object_name):
        objects = self.get_objects()
        print object_name
        print objects
        if objects.has_key(object_name):
            print "found object"
            object_view = objects[object_name]
            distance = object_view['distance']
            print distance
            if (distance < 5.0):
                return True
        return False

    def control__say(self, message):
       self.speech_bubble['text'] = message
       self.last_spoke = 0

    def talk_to_agent(self, agentName, message):
        self.agent_simulator.communicate(self.name, agentName, message)

    def control__pick_up_with_right_hand(self, pick_up_object=None):
        if not pick_up_object:
            d = self.raytrace_getAllObjectsInView()
            if len(d) > 0:
                pick_up_object = d.keys()[0]
            else:
                print "no objects in view to pick up"
                return
        print "attempting to pick up " + pick_up_object.name + " with right hand.\n"
        if self.right_hand_holding_object:
            return 'right hand is already holding ' + self.right_hand_holding_object.getName() + '.'
        if d[pick_up_object] < 5.0:
            if pick_up_object.getNetTag('heldBy') == '':
                pick_up_object.wrtReparentTo(self.player_right_hand)
                # pick_up_object.setPos(0, 0, 0)
                #pick_up_object.setHpr(0, 0, 0)
                self.right_hand_holding_object = pick_up_object
                pick_up_object.setTag('heldBy', self.name)
                print "sucess!"
                print self.player_right_hand.getPos()
                print pick_up_object.getPos()
                return 'success'
            else:
                print "Object being held by " + str(pick_up_object.node().getTag('heldBy'))
                return 'object (' + pick_up_object.name + ') is already held by something or someone.'
        else:
            print "Object not graspable, dist=" + str(d[pick_up_object])
            return 'object (' + pick_up_object.name + ') is not graspable (i.e. in view and close enough).'

    def control__put_object_in_empty_left_hand(self, object_name):
        if (self.left_hand_holding_object is not False):
            return False
        world_object = self.agent_simulator.world_objects[object_name]
        world_object.wrtReparentTo(self.player_left_hand)
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
        world_object.clearTag('heldBy')
        self.right_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.render)
        world_object.setHpr(0, 0, 0)
        #world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def control__drop_from_left_hand(self):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is False:
            return 'left hand is not holding an object.'
        world_object = self.left_hand_holding_object
        world_object.heldBy = None
        self.left_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.render)
        world_object.setHpr(0, 0, 0)
        world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def is_holding(self, object_name):
        return ((self.left_hand_holding_object  and (self.left_hand_holding_object.getName()  == object_name)) \
             or (self.right_hand_holding_object and (self.right_hand_holding_object.getName() == object_name)))

    def empty_hand(self):
        if (self.left_hand_holding_object is False):
            return self.player_left_hand
        elif (self.right_hand_holding_object is False):
            return self.player_right_hand
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
                    if (empty_hand == self.player_left_hand):
                        self.put_object_in_empty_left_hand(new_object_name)
                    elif (empty_hand == self.player_right_hand):
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


    def control__use_aimed(self):
        """
        Try to use the object that we aim at.
        A similar mechanics can be used to create a gun.

        Note the usage of the doRaycast method from the odeWorldManager.
        """
        dir = render.getRelativeVector(self.fov, Vec3(0, 1.0, 0))
        pos = self.fov.getPos(render) 
        print "relative vector", pos
        # FIXME: work with non-ODE
        return
        #self.aimRay.set(pos, dir)

        # raycast
        closestEntry, closestGeom = self.worldManager.doRaycast(self.aimRay, [self.capsuleGeom])
        if not closestGeom:
            return
        print "Closest geom", closestEntry
        data = self.worldManager.getGeomData(closestGeom)
        print data.name
        if data.selectionCallback:
            data.selectionCallback(self, dir)


    def sense__get_position(self):
        x,y,z = self.actor.getPos()
        h,p,r = self.actor.getHpr()
        #FIXME
        # neck is not positioned in Blockman nh,np,nr = self.agents[agent_id].actor_neck.getHpr()
        left_hand_obj = "" 
        right_hand_obj = "" 
        if self.left_hand_holding_object:  left_hand_obj = self.left_hand_holding_object.getName()
        if self.right_hand_holding_object: right_hand_obj = self.right_hand_holding_object.getName()
        return {'body_x': x, 'body_y': y, 'body_z': z,'body_h':h,\
                'body_p': p, 'body_r': r,  'in_left_hand': left_hand_obj, 'in_right_hand':right_hand_obj}
        #'neck_h':nh,'neck_p':np,'neck_r':nr,

    def sense__get_vision(self):
        return []
        # FIXME: this screenshot function causes a crash
        base.win.saveScreenshot( Filename( 'driving scene 2.png' ) )
        def make_screenshot(widthPixels=100,heightPixels=100): 
            tex=Texture() 
            width=widthPixels*4 
            height=heightPixels*4
            mybuffer=base.win.makeTextureBuffer('ScreenShotBuff',width,height,tex,True)  
            dis = mybuffer.makeDisplayRegion()
            cam=Camera('ScreenShotCam') 
            cam.setLens(self.agents[self.agentNum].fov.node().getLens().makeCopy()) 
            cam.getLens().setAspectRatio(width/height) 
            mycamera = base.makeCamera(mybuffer,useCamera=self.agents[self.agentNum].fov) 
            myscene = base.render 
            dis.setCamera(self.agents[self.agentNum].fov)
            mycamera.node().setScene(myscene) 
            print "a" 
            base.graphicsEngine.renderFrame() 
            print "a" 
            tex = mybuffer.getTexture() 
            print "a" 
            mybuffer.setActive(False) 
            print "a" 
            tex.write("screenshots/ralph_screen_"+str(time())+".jpg")
            print "a" 
            base.graphicsEngine.removeWindow(mybuffer)
        # TODO: not yet implemented (needs to print out and read image from camera)
        make_screenshot()
        return []# str(self.agent.fov.node().getCameraMask())

    def sense__get_objects(self):
        return self.get_objects()

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

    def addAction(self, timeStamp, action, args):
        self.queue.append((timeStamp, action, args))
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)

    def getActionsSince(self, timeStamp):
        actions = []
        for ts, a, args in self.queue:
            if ts >= timeStamp:
                actions.append((ts, a, args))
        return actions
        

    def updateOld(self, stepSize):
        if self.isSitting:
            if inputState.isSet("forward"):
                self.standUpFromChair()
            return

        elif self.isDisabled:
            return

        moveAtSpeed = 10.0
        self.speed = [0.0, 0.0]
    
        if (self.controlMap["turn_left"]!=0):
                self.setH(self.actor.getH() + stepSize*220)
        if (self.controlMap["turn_right"]!=0):
            if 0:# useAngularForces:
                fn = ForceNode("avf")
                avfn = NodePath(fn)
                avfn.reparentTo(self.geom)
                avfn.reparentTo(render)
                avf = AngularVectorForce(-1,0,0)
                fn.addForce(avf)
                actorNode.getPhysical(0).addAngularForce(avf)
            else:
                self.setH(self.actor.getH() - stepSize*220)
        if (self.controlMap["move_forward"]!=0):     self.speed[1] = moveAtSpeed
        if (self.controlMap["move_backward"]!=0):    self.speed[1] = -moveAtSpeed
        if (self.controlMap["move_left"]!=0):        self.speed[0] = -moveAtSpeed
        if (self.controlMap["move_right"]!=0):       self.speed[0] = moveAtSpeed
        if (self.controlMap["look_left"]!=0):      
            self.player_neck.setR(bound(self.player_neck.getR(),-60,60)+1*(stepSize*50))
        if (self.controlMap["look_right"]!=0):
            self.player_neck.setR(bound(self.player_neck.getR(),-60,60)-1*(stepSize*50))
        if (self.controlMap["look_up"]!=0):
            self.player_neck.setP(bound(self.player_neck.getP(),-60,80)+1*(stepSize*50))
        if (self.controlMap["look_down"]!=0):
            self.player_neck.setP(bound(self.player_neck.getP(),-60,80)-1*(stepSize*50))

        if inputState.isSet("crouch") or self.crouchLock:
            self.camH = self.crouchCamH
            PhysicsCharacterController.crouch(self)
        else:
            PhysicsCharacterController.crouchStop(self)
            self.camH = self.walkCamH

        PhysicsCharacterController.update(self, stepSize)
        # allow dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += stepSize
        self.speech_bubble['text_bg']=(1,1,1,1/(2*self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(2*self.last_spoke+0.01))
        if self.last_spoke > 2:
            self.speech_bubble['text'] = ""

        # update animation
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
            self.current_frame_count = self.current_frame_count + (stepSize*10000.0)
            while (self.current_frame_count >= total_frame_num + 1):
                self.current_frame_count -= total_frame_num
                self.actor.pose('walk', self.current_frame_count)


    def setWalkSpeed(self, forward, jump, reverse, rotate):
        assert self.notify.debugStateCall(self)
        self.avatarControlForwardSpeed=forward
        self.avatarControlJumpForce=jump
        self.avatarControlReverseSpeed=reverse
        self.avatarControlRotateSpeed=rotate

    def getSpeeds(self):
        #assert self.debugPrint("getSpeeds()")
        return (self.speed, self.rotationSpeed, self.slideSpeed)

    def getIsAirborne(self):
        return self.isAirborne

    def setAvatar(self, avatar):
        self.avatar = avatar
        if avatar is not None:
            pass # setup the avatar

    def setupRay(self, bitmask, floorOffset, reach):
        assert self.notify.debugStateCall(self)
        # This is a ray cast from your head down to detect floor polygons.
        # This ray start is arbitrarily high in the air.  Feel free to use
        # a higher or lower value depending on whether you want an avatar
        # that is outside of the world to step up to the floor when they
        # get under valid floor:
        cRay = CollisionRay(0.0, 0.0, CollisionHandlerRayStart, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('GW.cRayNode')
        cRayNode.addSolid(cRay)
        self.cRayNodePath = self.avatarNodePath.attachNewNode(cRayNode)
        cRayNode.setFromCollideMask(bitmask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())

        # set up floor collision mechanism
        self.lifter = CollisionHandlerGravity()
        #self.lifter = CollisionHandlerHighestEvent()
        self.lifter.setLegacyMode(self._legacyLifter)
        self.lifter.setGravity(self.__gravity)
        self.lifter.addInPattern("enter%in")
        self.lifter.addAgainPattern("again%in")
        self.lifter.addOutPattern("exit%in")
        self.lifter.setOffset(floorOffset)
        self.lifter.setReach(reach)

        # Limit our rate-of-fall with the lifter.
        # If this is too low, we actually "fall" off steep stairs
        # and float above them as we go down. I increased this
        # from 8.0 to 16.0 to prevent this
        #self.lifter.setMaxVelocity(16.0)

        self.lifter.addCollider(self.cRayNodePath, self.avatarNodePath)

    def setupWallSphere(self, bitmask, avatarRadius):
        """
        Set up the collision sphere
        """
        assert self.notify.debugStateCall(self)
        # This is a sphere on the ground to detect collisions with
        # walls, but not the floor.
        self.avatarRadius = avatarRadius
        cSphere = CollisionSphere(0.0, 0.0, avatarRadius, avatarRadius)
        cSphereNode = CollisionNode('GW.cWallSphereNode')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = self.avatarNodePath.attachNewNode(cSphereNode)

        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())

        # set up collision mechanism
        if config.GetBool('want-fluid-pusher', 0):
            self.pusher = CollisionHandlerFluidPusher()
        else:
            self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(cSphereNodePath, self.avatarNodePath)
        self.cWallSphereNodePath = cSphereNodePath

    def setupEventSphere(self, bitmask, avatarRadius):
        """
        Set up the collision sphere
        """
        assert self.notify.debugStateCall(self)
        # This is a sphere a little larger than the wall sphere to
        # trigger events.
        self.avatarRadius = avatarRadius
        cSphere = CollisionSphere(0.0, 0.0, avatarRadius-0.1, avatarRadius*1.04)
        # Mark it intangible just to emphasize its non-physical purpose.
        cSphere.setTangible(0)
        cSphereNode = CollisionNode('GW.cEventSphereNode')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = self.avatarNodePath.attachNewNode(cSphereNode)

        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())

        # set up collision mechanism
        self.event = CollisionHandlerEvent()
        self.event.addInPattern("enter%in")
        self.event.addOutPattern("exit%in")
        self.cEventSphereNodePath = cSphereNodePath

    def setupFloorSphere(self, bitmask, avatarRadius):
        """
        Set up the collision sphere
        """
        assert self.notify.debugStateCall(self)
        # This is a tiny sphere concentric with the wallSphere to keep
        # us from slipping through floors.
        self.avatarRadius = avatarRadius
        cSphere = CollisionSphere(0.0, 0.0, avatarRadius, 0.01)
        cSphereNode = CollisionNode('GW.cFloorSphereNode')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = self.avatarNodePath.attachNewNode(cSphereNode)

        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())

        # set up collision mechanism
        self.pusherFloorhandler = CollisionHandlerPusher()
        self.pusherFloor.addCollider(cSphereNodePath, self.avatarNodePath)
        self.cFloorSphereNodePath = cSphereNodePath

    def setWallBitMask(self, bitMask):
        self.wallBitmask = bitMask

    def setFloorBitMask(self, bitMask):
        self.floorBitmask = bitMask

    def swapFloorBitMask(self, oldMask, newMask):
        self.floorBitmask = self.floorBitmask &~ oldMask
        self.floorBitmask |= newMask

        if self.cRayNodePath and not self.cRayNodePath.isEmpty():
            self.cRayNodePath.node().setFromCollideMask(self.floorBitmask)

    def setGravity(self, gravity):
        self.__gravity = gravity
        self.lifter.setGravity(self.__gravity)

    def getGravity(self, gravity):
        return self.__gravity

    def initializeCollisions(self, collisionTraverser, avatarNodePath,
            avatarRadius = 1.4, floorOffset = 1.0, reach = 1.0):
        """
        floorOffset is how high the avatar can reach.  I.e. if the avatar
            walks under a ledge that is <= floorOffset above the ground (a
            double floor situation), the avatar will step up on to the
            ledge (instantly).

        Set up the avatar collisions
        """
        assert self.notify.debugStateCall(self)

        assert not avatarNodePath.isEmpty()
        self.avatarNodePath = avatarNodePath

        self.cTrav = collisionTraverser

        self.setupRay(self.floorBitmask, floorOffset, reach)
        self.setupWallSphere(self.wallBitmask, avatarRadius)
        self.setupEventSphere(self.wallBitmask, avatarRadius)
        if self.wantFloorSphere:
            self.setupFloorSphere(self.floorBitmask, avatarRadius)

        self.setCollisionsActive(1)

    def setTag(self, key, value):
        self.cEventSphereNodePath.setTag(key, value)

    def setAirborneHeightFunc(self, unused_parameter):
        assert self.notify.debugStateCall(self)
        self.getAirborneHeight = self.lifter.getAirborneHeight

    def getAirborneHeight(self):
        assert self.notify.debugStateCall(self)
        self.lifter.getAirborneHeight()

    def setAvatarPhysicsIndicator(self, indicator):
        """
        indicator is a NodePath
        """
        assert self.notify.debugStateCall(self)
        self.cWallSphereNodePath.show()

    def deleteCollisions(self):
        assert self.notify.debugStateCall(self)
        del self.cTrav

        self.cWallSphereNodePath.removeNode()
        del self.cWallSphereNodePath
        if self.wantFloorSphere:
            self.cFloorSphereNodePath.removeNode()
            del self.cFloorSphereNodePath

        del self.pusher
        # del self.pusherFloor
        del self.event
        del self.lifter

        del self.getAirborneHeight

    def setCollisionsActive(self, active = 1):
        assert self.notify.debugStateCall(self)
        if self.collisionsActive != active:
            self.collisionsActive = active
            # Each time we change the collision geometry, make one
            # more pass to ensure we aren't standing in a wall.
            self.oneTimeCollide()
            # make sure we have a shadow traverser
            base.initShadowTrav()
            if active:
                if 1:
                    # Please let skyler or drose know if this is causing a problem
                    # This is a bit of a hack fix:
                    self.avatarNodePath.setP(0.0)
                    self.avatarNodePath.setR(0.0)
                self.cTrav.addCollider(self.cWallSphereNodePath, self.pusher)
                if self.wantFloorSphere:
                    self.cTrav.addCollider(self.cFloorSphereNodePath, self.pusherFloor)
                # Add the lifter to the shadow traverser, which runs after
                # our traverser. This prevents the "fall through wall and
                # off ledge" bug. The problem was that we couldn't control
                # which collided first, the wall pusher or the lifter, if
                # they're in the same collision traverser. If the lifter
                # collided first, we'd start falling before getting pushed
                # back behind the wall.
                base.shadowTrav.addCollider(self.cRayNodePath, self.lifter)

                if self.earlyEventSphere:
                    # If we want to trigger the events at the same
                    # time as we intersect walls (e.g. Toontown, for
                    # backward compatibility issues), add the event
                    # sphere to the main traverser.  This allows us to
                    # hit door triggers that are just slightly behind
                    # the door itself.
                    self.cTrav.addCollider(self.cEventSphereNodePath, self.event)
                else:
                    # Normally, we'd rather trigger the events after
                    # the pusher has had a chance to fix up our
                    # position, so we never trigger things that are
                    # behind other polygons.
                    base.shadowTrav.addCollider(self.cEventSphereNodePath, self.event)

            else:
                if hasattr(self, 'cTrav'):
                    self.cTrav.removeCollider(self.cWallSphereNodePath)
                    if self.wantFloorSphere:
                        self.cTrav.removeCollider(self.cFloorSphereNodePath)
                    self.cTrav.removeCollider(self.cEventSphereNodePath)
                base.shadowTrav.removeCollider(self.cEventSphereNodePath)
                base.shadowTrav.removeCollider(self.cRayNodePath)

    def getCollisionsActive(self):
        assert self.debugPrint("getCollisionsActive() returning=%s"%(
            self.collisionsActive,))
        return self.collisionsActive

    def placeOnFloor(self):
        """
        Make a reasonable effor to place the avatar on the ground.
        For example, this is useful when switching away from the
        current walker.
        """
        assert self.notify.debugStateCall(self)
        self.oneTimeCollide()
        self.avatarNodePath.setZ(self.avatarNodePath.getZ()-self.lifter.getAirborneHeight())

    def oneTimeCollide(self):
        """
        Makes one quick collision pass for the avatar, for instance as
        a one-time straighten-things-up operation after collisions
        have been disabled.
        """
        assert self.notify.debugStateCall(self)
        if not hasattr(self, 'cWallSphereNodePath'):
            return
        self.isAirborne = 0
        self.mayJump = 1
        tempCTrav = CollisionTraverser("oneTimeCollide")
        tempCTrav.addCollider(self.cWallSphereNodePath, self.pusher)
        if self.wantFloorSphere:
            tempCTrav.addCollider(self.cFloorSphereNodePath, self.event)
        tempCTrav.addCollider(self.cRayNodePath, self.lifter)
        tempCTrav.traverse(render)

    def setMayJump(self, task):
        """
        This function's use is internal to this class (maybe I'll add
        the __ someday).  Anyway, if you want to enable or disable
        jumping in a general way see the ControlManager (don't use this).
        """
        assert self.notify.debugStateCall(self)
        self.mayJump = 1
        return Task.done

    def startJumpDelay(self, delay):
        assert self.notify.debugStateCall(self)
        if self.jumpDelayTask:
            self.jumpDelayTask.remove()
        self.mayJump = 0
        self.jumpDelayTask=taskMgr.doMethodLater(
            delay,
            self.setMayJump,
            "jumpDelay-%s"%id(self))

    def addBlastForce(self, vector):
        self.lifter.addVelocity(vector.length())

    def displayDebugInfo(self):
        """
        For debug use.
        """
        onScreenDebug.add("w controls", "GravityWalker")

        onScreenDebug.add("w airborneHeight", self.lifter.getAirborneHeight())
        onScreenDebug.add("w falling", self.falling)
        onScreenDebug.add("w isOnGround", self.lifter.isOnGround())
        #onScreenDebug.add("w gravity", self.lifter.getGravity())
        #onScreenDebug.add("w jumpForce", self.avatarControlJumpForce)
        onScreenDebug.add("w contact normal", self.lifter.getContactNormal().pPrintValues())
        onScreenDebug.add("w mayJump", self.mayJump)
        onScreenDebug.add("w impact", self.lifter.getImpactVelocity())
        onScreenDebug.add("w velocity", self.lifter.getVelocity())
        onScreenDebug.add("w isAirborne", self.isAirborne)
        onScreenDebug.add("w hasContact", self.lifter.hasContact())

    def update(self, task):
        self.oneTimeCollide( ) 
        """
        Check on the arrow keys and update the avatar.
        """
        # get the button states:
        
        

        run = 0#inputState.isSet("run")
        forward = self.controlMap['move_forward'] != 0
        reverse = self.controlMap['move_backward'] != 0
        turnLeft =self.controlMap['turn_left'] != 0
        turnRight =self.controlMap['turn_right'] != 0
        slideLeft = self.controlMap['move_left'] != 0
        slideRight = self.controlMap['move_right'] != 0
        jump = self.controlMap['jump'] != 0

        # Determine what the speeds are based on the buttons:
        self.speed=(forward and self.avatarControlForwardSpeed or
                    reverse and -self.avatarControlReverseSpeed)
        # Slide speed is a scaled down version of forward speed
        # Note: you can multiply a factor in here if you want slide to
        # be slower than normal walk/run. Let's try full speed.
        #self.slideSpeed=(slideLeft and -self.avatarControlForwardSpeed*0.75 or
        #                 slideRight and self.avatarControlForwardSpeed*0.75)
        self.slideSpeed=(reverse and slideLeft and -self.avatarControlReverseSpeed*0.75 or
                         reverse and slideRight and self.avatarControlReverseSpeed*0.75 or
                         slideLeft and -self.avatarControlForwardSpeed*0.75 or
                         slideRight and self.avatarControlForwardSpeed*0.75)
        self.rotationSpeed=not (slideLeft or slideRight) and (
                (turnLeft and self.avatarControlRotateSpeed) or
                (turnRight and -self.avatarControlRotateSpeed))

        if self.speed and self.slideSpeed:
            self.speed *= GravityWalker.DiagonalFactor
            self.slideSpeed *= GravityWalker.DiagonalFactor


        if self.needToDeltaPos:
            self.setPriorParentVector()
            self.needToDeltaPos = 0
        if self.wantDebugIndicator:
            self.displayDebugInfo()
        if self.lifter.isOnGround():
            if self.isAirborne:
                self.isAirborne = 0
                assert self.debugPrint("isAirborne 0 due to isOnGround() true")
                impact = self.lifter.getImpactVelocity()
                if impact < -30.0:
                    messenger.send("jumpHardLand")
                    self.startJumpDelay(0.3)
                else:
                    messenger.send("jumpLand")
                    if impact < -5.0:
                        self.startJumpDelay(0.2)
                    # else, ignore the little potholes.
            assert self.isAirborne == 0
            self.priorParent = Vec3.zero()
            if jump and self.mayJump:
                # The jump button is down and we're close
                # enough to the ground to jump.
                self.lifter.addVelocity(self.avatarControlJumpForce)
                messenger.send("jumpStart")
                self.isAirborne = 1
                assert self.debugPrint("isAirborne 1 due to jump")
        else:
            if self.isAirborne == 0:
                assert self.debugPrint("isAirborne 1 due to isOnGround() false")
            self.isAirborne = 1

        self.__oldPosDelta = self.avatarNodePath.getPosDelta(render)
        # How far did we move based on the amount of time elapsed?
        self.__oldDt = ClockObject.getGlobalClock().getDt()
        dt=self.__oldDt

        # Check to see if we're moving at all:
        self.moving = self.speed or self.slideSpeed or self.rotationSpeed or (self.priorParent!=Vec3.zero())
        if self.moving:
            distance = dt * self.speed
            slideDistance = dt * self.slideSpeed
            rotation = dt * self.rotationSpeed

            # Take a step in the direction of our previous heading.
            if distance or slideDistance or self.priorParent != Vec3.zero():
                # rotMat is the rotation matrix corresponding to
                # our previous heading.
                rotMat=Mat3.rotateMatNormaxis(self.avatarNodePath.getH(), Vec3.up())
                if self.isAirborne:
                    forward = Vec3.forward()
                else:
                    contact = self.lifter.getContactNormal()
                    forward = contact.cross(Vec3.right())
                    # Consider commenting out this normalize.  If you do so
                    # then going up and down slops is a touch slower and
                    # steeper terrain can cut the movement in half.  Without
                    # the normalize the movement is slowed by the cosine of
                    # the slope (i.e. it is multiplied by the sign as a
                    # side effect of the cross product above).
                    forward.normalize()
                self.vel=Vec3(forward * distance)
                if slideDistance:
                    if self.isAirborne:
                        right = Vec3.right()
                    else:
                        right = forward.cross(contact)
                        # See note above for forward.normalize()
                        right.normalize()
                    self.vel=Vec3(self.vel + (right * slideDistance))
                self.vel=Vec3(rotMat.xform(self.vel))
                step=self.vel + (self.priorParent * dt)
                self.avatarNodePath.setFluidPos(Point3(
                        self.avatarNodePath.getPos()+step))
            self.avatarNodePath.setH(self.avatarNodePath.getH()+rotation)
        else:
            self.vel.set(0.0, 0.0, 0.0)
        if self.moving or jump:
            messenger.send("avatarMoving")
        return Task.cont

    def doDeltaPos(self):
        assert self.notify.debugStateCall(self)
        self.needToDeltaPos = 1

    def setPriorParentVector(self):
        assert self.notify.debugStateCall(self)
        if __debug__:
            onScreenDebug.add("__oldDt", "% 10.4f"%self.__oldDt)
            onScreenDebug.add("self.__oldPosDelta",
                              self.__oldPosDelta.pPrintValues())
        # avoid divide by zero crash - grw
        if self.__oldDt == 0:
            velocity = 0
        else:
            velocity = self.__oldPosDelta*(1.0/self.__oldDt)
        self.priorParent = Vec3(velocity)
        if __debug__:
            if self.wantDebugIndicator:
                onScreenDebug.add("priorParent", self.priorParent.pPrintValues())

    def reset(self):
        assert self.notify.debugStateCall(self)
        self.lifter.setVelocity(0.0)
        self.priorParent=Vec3.zero()

    def getVelocity(self):
        return self.vel


    def flushEventHandlers(self):
        if hasattr(self, 'cTrav'):
            self.pusher.flush()
            if self.wantFloorSphere:
                self.floorPusher.flush()
            self.event.flush()
        self.lifter.flush() # not currently defined or needed


class Picker(DirectObject.DirectObject):
    """Picker class derived from http://www.panda3d.org/phpbb2/viewtopic.php?p=4532&sid=d5ec617d578fbcc4c4db0fc68ee87ac0"""
    def __init__(self, camera, worldObjects, tag = 'pickable', value = 'true'):
        self.camera = camera
        self.tag = tag
        self.value = value
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)

        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)

        self.picker.addCollider(self.pickerNP, self.queue)
        self.worldObjects = worldObjects

    def pick(self, pos):
        self.pickerRay.setFromLens(self.camera.node(), pos[0], pos[1])
        self.picker.traverse(render)
        if self.queue.getNumEntries() > 1:
            self.queue.sortEntries()
            parent = self.queue.getEntry(1).getIntoNodePath().getParent()
            point = self.queue.getEntry(1).getSurfacePoint(self.camera)
            dist = math.sqrt(point.getX()**2+point.getY()**2+point.getZ()**2)

            while parent != render:
                if(self.tag == None):
                    return (parent, dist)
                elif parent.getTag(self.tag) == self.value:
                    name = str(parent)
                    return (self.worldObjects[name[name.rfind("IsisObject"):]], dist)
                else:
                    parent = parent.getParent()
        return None


    def getObjectsInView(self, xpoints = 32, ypoints = 24):
        objects = {}
        for x in frange(-1, 1, 2.0/xpoints):
            for y in frange(-1, 1, 2.0/ypoints):
                o = self.pick((x, y))
                if o and (o[0] not in objects or o[1] < objects[o[0]]):
                    objects[o[0]] = o[1]
        return objects
        """
        GravityWalker.py is for avatars.

        A walker control such as this one provides:
            - creation of the collision nodes
            - handling the keyboard and mouse input for avatar movement
            - moving the avatar

        it does not:
            - play sounds
            - play animations

        although it does send messeges that allow a listener to play sounds or
        animations based on walker events.
        """
