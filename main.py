#!/usr/bin/env python
""" IsisWorld is a simulated world for testing commonsense reasoning systems

For more details, see: http://mmp.mit.edu/isisworld/
"""

ISIS_VERSION = 0.4

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", 
"""sync-video 0
load-display pandagl
aux-display tinydisplay
winow-title "IsisWorld"
win-size 800 600
textures-power-2 none 
basic-shaders-only f""")

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from direct.filter.CommonFilters import CommonFilters 
from direct.gui.DirectGui import DirectEntry
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

from simulator.floating_camera import FloatingCamera
from simulator.skydome2 import *
from simulator.physics import *
from simulator.ralph import *
from simulator.object_loader import *
from simulator.actions import *
from xmlrpc.xmlrpc_server import HomeSim_XMLRPC_Server
from xmlrpc.command_handler import Command_Handler
from random import randint, random
import threading, sys
        
class IsisWorld(ShowBase):
    """ IsisWorld is the simulator class inheriting from Panda3D's ShowBase
    class, which inherits from the DirectObject.

    Among other things, this instantiates a taskMgr which can be launched
    by a single call to `run()`.

    Several variables are attributes of the ShowBase instance, including

        - base
        - render: the default 3D scene graph
        - render2d: the default 2D scene graph, for GUI elements
              - (-1,0,-1) is lower left-hand corner
              - (1,0,1) is upper right hand corner
        - camera
        - messenger
        - taskMgr

    For a complete list, see: http://www.panda3d.org/wiki/index.php/ShowBase
    """
    def __init__(self):
        ShowBase.__init__(self)
        # load the objects into the world
        self.setupEnvironment(debug=False)
        self.worldObjects = {}
        #self.worldObjects.update(load_objects_in_world(self.worldManager,render, self.worldObjects))
        # start physics manager
        # this is defined in simulator/physics.py
        self.worldManager = PhysicsWorldManager()
        # setup components
        self.setupMap()
        self.setupLights()
        self.worldManager.startPhysics()
        self.setupAgent()
        self.setupCameras()
        self.setupControls()

    def setupEnvironment(self, debug=False):
        """ Sets up the environment variables and starts the server """
        render.setShaderAuto()
        base.setFrameRateMeter(True)
        base.setBackgroundColor(.2, .2, .2)
        base.camLens.setFov(75)
        base.camLens.setNear(0.2)
        base.disableMouse()
        # debugging stuff
        if debug:
            # display all events
            messenger.toggleVerbose()
        # setup the server
        # xmlrpc server command handler
        xmlrpc_command_handler = Command_Handler(self)
        # xmlrpc server
        self.server_object = HomeSim_XMLRPC_Server()
        self.server = self.server_object.server
        self.server.register_function(xmlrpc_command_handler.command_handler,'do')
        self.server_thread = threading.Thread(group=None, target=self.server.serve_forever, name='xmlrpc')
        self.server_thread.start()

              
 
    def setupMap(self):
	""" The map consists of a plane, the "ground" that stretches to infinity
	and a dome, the "sky" that sits concavely on the ground.

	For the ground component, a separate physics module must be created 
	so that the characters and objects do not fall through it.

	This is done by calling the physics module:  physicsModule.setupGround()"""
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture("./textures/env_ground.jpg")
        cm.setFrame(-100, 100, -100, 100)
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        groundNP.setTransparency(TransparencyAttrib.MAlpha)

        # TODO: make sky inverted cylinder?
        self.worldManager.setupGround(groundNP)
        self.skydomeNP = SkyDome2(render)
        self.skydomeNP.setStandardControl()
        self.skydomeNP.att_skycolor.setColor(Vec4(0.3,0.3,0.3,1))
        self.skydomeNP.setPos(Vec3(0,0,-500))
        def timeUpdated(task):
            self.skydomeNP.skybox.setShaderInput('time', task.time)
            return task.cont
        taskMgr.add(timeUpdated, "timeUpdated")

        """
        Get the map's panda node. This will allow us to find the objects
        that the map consists of.
        """
        self.map = loader.loadModel("./models3/kitchen")
        self.map.reparentTo(render)
        self.mapNode = self.map.find("-PandaNode")
        self.room = self.mapNode.find("Wall")
        #self.worldManager.addItem(PhysicsTrimesh(name="Wall",world=self.worldManager.world, space=self.worldManager.space,pythonObject=self.room,density=800,surfaceFriction=10),False)
        self.map.node().setIntoCollideMask(WALLMASK)

        """
        Add a table to the room """

        self.table = loader.loadModel("./models3/table/table")
        self.table.reparentTo(self.map)
        self.table.setPosHpr(0,2.8,0,0,0,0)
        self.table.setScale(0.007)

        self.worldObjects['table'] = self.table

        #self.worldManager.addItem(PhysicsBox(world=self.worldManager.world, space=self.worldManager.space,pythonObject=self.table,density=800,surfaceFriction=10),False)


        """
        Steps is yet another part of the map.
        Meant, obviously, to demonstrate the ability to climb stairs.
        """
        self.steps = self.mapNode.find("Steps")
        """
        Door functionality is also provided here.
        More on door in the appropriate file.
        """
        self.doorNP = self.mapNode.find("Door")
        #self.door = door(self.worldManager, self.doorNP)
        #self.worldObjects['door'] = door
        
        self.map.flattenStrong()
        self.table.flattenStrong()
        self.steps.flattenStrong()
        #self.doorNP.flattenStrong()

        
    def setupCameras(self):
        # Set up the camera 
        ### Set up displays and cameras ###
        self.floating_camera = FloatingCamera(self.agents[self.agentNum].actor)

        # set up picture in picture
        dr = base.camNode.getDisplayRegion(0)
        aspect_ratio = 16.0 / 9.0
        window = dr.getWindow()
        pip_size = 0.40 # percentage of width of screen
        dr_pip = window.makeDisplayRegion(1-pip_size,1,0,\
             (1.0 / aspect_ratio) * float(dr.getPixelWidth())/float(dr.getPixelHeight()) * pip_size)
        dr_pip.setCamera(self.agents[self.agentNum].fov)
        dr_pip.setSort(dr.getSort())
        dr_pip.setClearColor(VBase4(0, 0, 0, 1))
        dr_pip.setClearColorActive(True)
        dr_pip.setClearDepthActive(True)
        #self.agent.fov.node().getLens().setAspectRatio(aspect_ratio)
        dr_pip.setActive(1)


    def setupLights(self):
        alight = AmbientLight("ambientLight")
        alight.setColor(Vec4(.7, .7, .7, 1.0))
        alightNP = render.attachNewNode(alight)

        dlight = DirectionalLight("directionalLight")
        dlight.setDirection(Vec3(1, 1, -1))
        dlight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        dlightNP = render.attachNewNode(dlight)

        render.clearLight()
        render.setLight(alightNP)
        render.setLight(dlightNP)

    def setupAgent(self):
        # agentNum keeps track of the currently active visible
        # that the camera and fov follow
        self.agentNum = 0
        self.agents = []
        self.agentsNamesToIDs = {'Ralph':0, 'Lauren':1, 'David':2}
        self.agents.append(Ralph(base.worldManager, self, "Ralph"))
        #self.agents[0].actor.setPos(Vec3(-1,0,0))
        self.agents[0].control__say("Hi, I'm Ralph. Please build me.")

        self.agents.append(Ralph(base.worldManager, self, "Lauren"))
        #self.agents[1].actor.setPos(Vec3(-3,-3,0))
        self.agents[1].control__say("Hi, I'm Lauren. Please build me.")

        self.agents.append(Ralph(base.worldManager, self, "David"))
        #self.agents[2].actor.setPos(Vec3(3,-3,0))
        self.agents[2].control__say("Hi, I'm David. Please build me.")

        
    def setupControls(self):

        def relayAgentControl(command):
            """ Accepts an instruction issued through the bound keyboard commands
            because "self.agentNum" need to be revaluated at the time the command
            is issued, necessitating this helper function"""
            if self.actionController.hasAction(command):
                self.actionController.makeAgentDo(command, self.agents[self.agentNum])
            else:
                print "relayAgentControl: %s command not found in action controller" % (command)
                raise self.actionController

        text = "\n"
        text += "IsisWorld v%s\n" % (ISIS_VERSION)
        text += "\n\n"
        text += "\nPress [1] to toggle wire frame\n"
        text += "\nPress [2] to toggle texture\n"
        text += "\nPress [3] to switch agent\n"
        text += "\nPress [i] to hide/show this text\n"
        text += "\n[o] lists objects in agent's f.o.v.\n"
        text += "\n[Esc] to quit\n\n"
        # initialize actions
        self.actionController = ActionController("Version 1.0")
        self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True,keyboardBinding="arrow_left"))
        self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True,keyboardBinding="arrow_right"))
        self.actionController.addAction(IsisAction(commandName="move_forward",intervalAction=True,keyboardBinding="arrow_up"))
        self.actionController.addAction(IsisAction(commandName="move_backward",intervalAction=True,keyboardBinding="arrow_down"))
        self.actionController.addAction(IsisAction(commandName="look_right",intervalAction=True,keyboardBinding="l"))
        self.actionController.addAction(IsisAction(commandName="look_left",intervalAction=True,keyboardBinding="h"))
        self.actionController.addAction(IsisAction(commandName="look_up",intervalAction=True,keyboardBinding="k"))
        self.actionController.addAction(IsisAction(commandName="look_down",intervalAction=True,keyboardBinding="j"))
        self.actionController.addAction(IsisAction(commandName="jump",intervalAction=False,keyboardBinding="g"))
        self.actionController.addAction(IsisAction(commandName="use_aimed",intervalAction=False,keyboardBinding="u"))

        # initialze keybindings
        for keybinding, command in self.actionController.keyboardMap.items():
            print "adding command to ", keybinding, command
            base.accept(keybinding, relayAgentControl, [command])

        # add documentation
        for helpString in self.actionController.helpStrings:
            text += "\n%s\n" % (helpString)

        props = WindowProperties( )
        props.setTitle( 'IsisWorld v%s' % ISIS_VERSION )
        base.win.requestProperties( props )
        
        self.textObjectVisisble = True
        self.textObject = OnscreenText(
                text = text,
                fg = (.98, .9, .9, 1),
                bg = (.1, .1, .1, 0.8),
                pos = (-1.2, .9),
                scale = 0.04,
                align = TextNode.ALeft,
                wordwrap = 15,
        )
        def hideText():
            if self.textObjectVisisble:
                self.textObject.detachNode()
                self.textObjectVisisble = False
            else:
                self.textObject.reparentTo(aspect2d)
                self.textObjectVisisble = True

        def changeAgent():
            if (self.agentNum == (len(self.agents)-1)):
                self.agentNum = 0
                
            else:
                self.agentNum += 1
            self.setupCameras()
        # Accept some keys to move the camera.
        self.accept("a-up", self.floating_camera.setControl, ["right", 0])
        self.accept("a",    self.floating_camera.setControl, ["right", 1])
        self.accept("s-up", self.floating_camera.setControl, ["left",  0])
        self.accept("s",    self.floating_camera.setControl, ["left",  1])
        self.accept("d",    self.floating_camera.setControl, ["zoom-in",  1])
        self.accept("d-up", self.floating_camera.setControl, ["zoom-in",  0])
        self.accept("f",    self.floating_camera.setControl, ["zoom-out",  1])
        self.accept("f-up", self.floating_camera.setControl, ["zoom-out",  0])
        #if self.is_ralph == True:
        # control keys to move the character
         

        base.accept("o", hideText)

        # key input
        base.accept("1",              base.toggleWireframe, [])
        base.accept("2",              base.toggleTexture, [])
        base.accept("3",              changeAgent, [])
        self.accept("space",           self.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("o",               self.printObjects, []) # displays objects in field of view
        self.accept("p",               self.togglePaused)
        #self.accept("r",              self.reset_simulation)
        base.accept("escape",         sys.exit)
    
        self.teacher_utterances = [] # last message typed
        # main dialogue box
        def disable_keys(x):
            x.command_box.enterText("")
            x.command_box.suppressKeys=True
            x.command_box["frameColor"]=(0.631, 0.219, 0.247,1)

        def enable_keys(x):
            x.command_box["frameColor"]=(0.631, 0.219, 0.247,.25)
            x.command_box.suppressKeys=False

        def accept_message(message,x):
            x.teacher_utterances.append(message)
            x.command_box.enterText("")


        self.command_box = DirectEntry(pos=(-1.2,-0.95,-0.95), text_fg=(0.282, 0.725, 0.850,1), frameColor=(0.631, 0.219, 0.247,0.25), suppressKeys=1, initialText="enter text and hit return", enableEdit=0,scale=0.07, focus=0, focusInCommand=disable_keys, focusOutCommand=enable_keys, focusInExtraArgs=[self], focusOutExtraArgs=[self], command=accept_message, extraArgs=[self],  width=15, numLines=1)
        base.win.setClearColor(Vec4(0,0,0,1))

    def step_simulation(self,time=1):
	for agent in self.agents: agent.update(time)

    _GCLK=None
    _FT=None
    def togglePaused(self):
        if (self._GCLK == None):
          print "[pong] pausing..."
          base.disableParticles()
          self._GCLK=ClockObject.getGlobalClock()
          self._FT=self._GCLK.getFrameTime()
          self._GCLK.setMode(ClockObject.MSlave)
        else:
          self._GCLK.setRealTime(self._FT)
          self._GCLK.setMode(ClockObject.MNormal)
          base.enableParticles()
          self._GCLK=None
          print "[pong] restarting..."

    def get_camera_position(self):
        print base.camera.getPos()
        print base.camera.getHpr()

    def get_agent_position(self, agent_id=None):
        if agent_id == None:
            agent_id = self.agentNum
        x,y,z = self.agents[agent_id].actor.getPos()
        h,p,r = self.agents[agent_id].actor.getHpr()
        nh,np,nr = self.agents[agent_id].actor_neck.getHpr()
        left_hand_obj = "" 
        right_hand_obj = "" 
        if self.agents[agent_id].left_hand_holding_object:  left_hand_obj = self.agents[agent_id].left_hand_holding_object.getName()
        if self.agents[agent_id].right_hand_holding_object: right_hand_obj = self.agents[agent_id].right_hand_holding_object.getName()
        return {'body_x': x, 'body_y': y, 'body_z': z,'body_h':h,\
                'body_p': p, 'body_r': r, 'neck_h':nh,'neck_p':np,'neck_r':nr, 'in_left_hand': left_hand_obj, 'in_right_hand':right_hand_obj}

    def get_agent_vision(self,agent_id=None):
        if agent_id == None:
            agent_id = self.agentNum
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

    def get_objects(self, agent_id=None):
        if agent_id == None:
            agent_id = self.agentNum
        return self.agents[agent_id].get_objects()

    def get_utterances(self):
        """ Clear out the buffer of things that the teacher has typed,
        FIXME: perpahs these should be timestamped if they are not 
         at the right time? """
        utterances = self.teacher_utterances
        self.teacher_utterances = []
        return utterances


    def printObjects(self):
        text = "Objects in FOV: "+ ", ".join(self.get_objects().keys())
        print text


            
            


w = IsisWorld()

w.run()
