#!/usr/bin/env python


""" IsisWorld is a simulated world for testing commonsense reasoning systems

For more details, see: http://mmp.mit.edu/isisworld/
"""

ISIS_VERSION = 0.4
FRAME_RATE = 20

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", 
"""sync-video 0
load-display pandagl
aux-display tinydisplay
winow-title "IsisWorld"
win-size 800 600
clock-mode limited
#clock-frame-rate %i
textures-power-2 none 
basic-shaders-only f""" % FRAME_RATE )

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from direct.filter.CommonFilters import CommonFilters 
from direct.gui.DirectGui import DirectEntry, DirectButton
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

from simulator.floating_camera import FloatingCamera
from simulator.skydome2 import *
from simulator.physics import *
from simulator.ralph import *
from simulator.object_loader import *
from simulator.door import *
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
        #self.worldObjects.update(load_objects_in_world(self.physicsManager,render, self.worldObjects))
        # start physics manager

        self.inspectState = False
        # this is defined in simulator/physics.py
        self.physicsManager = PhysicsWorldManager()
        # setup components
        self.setupMap()
        self.setupLights()
        self.physicsManager.startPhysics()
        self.setupAgent()
        self.setupCameras()
        base.taskMgr.add(self.floating_camera.update_camera, 'update_camera')
        self.setupControls()

    def setupEnvironment(self, debug=False):
        """ Sets up the environment variables and starts the server """
        render.setShaderAuto()
        base.setFrameRateMeter(True)
        base.setBackgroundColor(.2, .2, .2)
        base.camLens.setFov(75)
        base.camLens.setNear(0.2)
        base.disableMouse()
        self._globalClock = ClockObject.getGlobalClock()
        self._globalClock.setMode(ClockObject.MLimited)
        self._globalClock.setFrameRate(FRAME_RATE)
        self._globalClock=None
        self._frameTime = None
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
        self.server_thread = threading.Thread(group=None, target=self.server.serve_forever, name='isisworld-xmlrpc')
        self.server_thread.start()

              
 
    def setupMap(self):
        """ The map consists of a plane, the "ground" that stretches to infinity
        and a dome, the "sky" that sits concavely on the ground.

        For the ground component, a separate physics module must be created 
        so that the characters and objects do not fall through it.

        This is done by calling the physics module:  physicsModule.setupGround()"""
        # parameters
        self.visualizeClouds = True 
        
        self.mapNode = None
        self.map = None
        self.room = None
        self.door = None
        self.doorNP = None
        
        self.physicsManager.setupGround(self)
        """
        Load Objects from '.isis' file """
        self.worldObjects.update(load_objects("./kitchen.isis", self.map, self.physicsManager))
        for name in self.worldObjects:
          self.worldObjects[name].flattenLight()
        """
        Door functionality is also provided here.
        More on door in the appropriate file.
        """
        self.doorNP = self.mapNode.find("Door")
        self.door = door(self.physicsManager, self.doorNP)
        self.worldObjects['door'] = door

        """ 
        Setup the skydome
        """
        """
        Moving clouds are pretty but computationally expensive 
        only visualize them if you have"""
        if self.visualizeClouds: 
            self.skydomeNP = SkyDome2(render,self.visualizeClouds)
            self.skydomeNP.setPos(Vec3(0,0,-500))
            self.skydomeNP.setStandardControl()
            self.skydomeNP.att_skycolor.setColor(Vec4(0.3,0.3,0.3,1))
            def timeUpdated(task):
                self.skydomeNP.skybox.setShaderInput('time', task.time)
                return task.cont
            taskMgr.add(timeUpdated, "timeUpdated")
        else:
            self.skydomeNP = SkyDome1(render,self.visualizeClouds)


        
    def setupCameras(self):
        # Set up the camera 
        ### Set up displays and cameras ###
        self.floating_camera = FloatingCamera(self.agents[self.agentNum].actor)
        base.camera.reparentTo(self.agents[self.agentNum].actor)
        # set up picture in picture
        dr = base.camNode.getDisplayRegion(0)
        aspect_ratio = 16.0 / 9.0
        window = dr.getWindow()
        pip_size = 0.40 # percentage of width of screen
        self.agentCamera = window.makeDisplayRegion(1-pip_size,1,0,\
             (1.0 / aspect_ratio) * float(dr.getPixelWidth())/float(dr.getPixelHeight()) * pip_size)
        self.agentCamera.setCamera(self.agents[self.agentNum].fov)
        self.agentCamera.setSort(dr.getSort())
        self.agentCamera.setClearColor(VBase4(0, 0, 0, 1))
        self.agentCamera.setClearColorActive(True)
        self.agentCamera.setClearDepthActive(True)
        #self.agent.fov.node().getLens().setAspectRatio(aspect_ratio)
        self.agentCamera.setActive(1)


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
        # add and initialize new agents
        for name in self.agentsNamesToIDs.keys():
            newAgent = Ralph(base.physicsManager, self, name)
            newAgent.control__say("Hi, I'm %s. Please build me." % name)
            #taskMgr.add(newAgent.update, "updateCharacter-%s" % name)
            self.agents.append(newAgent)

        
    def setupControls(self):

        def relayAgentControl(command):
            """ Accepts an instruction issued through the bound keyboard commands
            because "self.agentNum" need to be revaluated at the time the command
            is issued, necessitating this helper function"""
            if self.actionController.hasAction(command):
                self.actionController.makeAgentDo(self.agents[self.agentNum], command)
            else:
                print "relayAgentControl: %s command not found in action controller" % (command)
                raise self.actionController

        text = "\n"
        text += "IsisWorld v%s\n" % (ISIS_VERSION)
        text += "\n\n"
        text += "\nPress [1] to toggle wire frame"
        text += "\nPress [2] to toggle texture"
        text += "\nPress [3] to switch agent"
        text += "\nPress [i] to hide/show this text"
        text += "\n[o] lists objects in agent's f.o.v."
        text += "\n[Esc] to quit\n"
        # initialize actions
        self.actionController = ActionController("Version 0.1")
        #self.actionController.addAction(IsisAction(commandName="move_left",intervalAction=True,keyboardBinding="arrow_left"))
        #self.actionController.addAction(IsisAction(commandName="move_right",intervalAction=True,keyboardBinding="arrow_right"))
        #self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True))
        #self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True))
        self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True,keyboardBinding="arrow_left"))
        self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True,keyboardBinding="arrow_right"))
        self.actionController.addAction(IsisAction(commandName="move_forward",intervalAction=True,keyboardBinding="arrow_up"))
        self.actionController.addAction(IsisAction(commandName="move_backward",intervalAction=True,keyboardBinding="arrow_down"))
        self.actionController.addAction(IsisAction(commandName="look_right",intervalAction=True,keyboardBinding="l"))
        self.actionController.addAction(IsisAction(commandName="look_left",intervalAction=True,keyboardBinding="h"))
        self.actionController.addAction(IsisAction(commandName="look_up",intervalAction=True,keyboardBinding="k"))
        self.actionController.addAction(IsisAction(commandName="look_down",intervalAction=True,keyboardBinding="j"))
        self.actionController.addAction(IsisAction(commandName="jump",intervalAction=False,keyboardBinding="g"))
        self.actionController.addAction(IsisAction(commandName="say",intervalAction=False))
        self.actionController.addAction(IsisAction(commandName="sense",intervalAction=False))
        self.actionController.addAction(IsisAction(commandName="use_aimed",intervalAction=False,keyboardBinding="u"))

        # initialze keybindings
        for keybinding, command in self.actionController.keyboardMap.items():
            print "adding command to ", keybinding, command
            base.accept(keybinding, relayAgentControl, [command])

        # add documentation
        for helpString in self.actionController.helpStrings:
            text += "\n%s" % (helpString)

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
        
        b = DirectButton(pos=(-1.3,0.0,-0.95),text = ("Inspect", "click!", "rolling over", "disabled"), scale=0.05, command = self.toggleInspect)
        #base.accept("o", toggle)

        # key input
        base.accept("1",               base.toggleWireframe, [])
        base.accept("2",               base.toggleTexture, [])
        base.accept("3",               changeAgent, [])
        self.accept("space",           self.step_simulation, [.1]) # argument is amount of second to advance
        #self.accept("o",               self.printObjects, []) # displays objects in field of view
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
            if message.strip() == "open":
                self.door.select()
                #self.door.open()
            x.teacher_utterances.append(message)
            x.command_box.enterText("")


        self.command_box = DirectEntry(pos=(-1.2,-0.95,-0.95), text_fg=(0.282, 0.725, 0.850,1), frameColor=(0.631, 0.219, 0.247,0.25), suppressKeys=1, initialText="enter text and hit return", enableEdit=0,scale=0.07, focus=0, focusInCommand=disable_keys, focusOutCommand=enable_keys, focusInExtraArgs=[self], focusOutExtraArgs=[self], command=accept_message, extraArgs=[self],  width=15, numLines=1)
        base.win.setClearColor(Vec4(0,0,0,1))

    def step_simulation(self,stepTime=2):
        if self._globalClock != None:
            self.togglePaused()
            gc = ClockObject.getGlobalClock()
            #time1 = gc.getFrameTime()
            time.sleep(stepTime)
            #print "Framerate", FRAME_RATE, time1
            #while(True):
            #    time2 = gc.getFrameTime()
            #    if (time2-time1)/FRAME_RATE > stepTime:
            #        break
            #    else:
            #        print (time2-time1), (time2-time1)/FRAME_RATE
            self.togglePaused()

    def toggleInspect(self):
        self.inspectState = not self.inspectState
        print "Inspect State", self.inspectState
        if self.inspectState:
            self.agentCamera.setActive(0)
            #base.camera.setPos(self.agents[self.agentNum].actor.getPos()+Vec3(2,0,0))
            #base.camera.setHpr(0,0,0)
            base.camera.lookAt(self.agents[self.agentNum].actor.getX(),self.agents[self.agentNum].actor.getY()+2,0)
            active_agent = self.agents[self.agentNum].actor
            for child in render.getChildren():
                if child != active_agent and child.getName()[-5:] != "Light" and child.getName() != "ground": 
                    child.hide()
                    print child.getName()[-5:]
                    print "removing", child
        else:
            for child in render.getChildren(): child.show()

    def togglePaused(self):
        """ by default, the simulator is unpaused/running.
        toggling it will remove each ralph's update() function
        from the task manager"""
        if (self._globalClock == None):
          print "[IsisWorld] Pausing Simulator"
          #for name in self.agentsNamesToIDs.keys():
          #   taskMgr.remove("updateCharacter-%s" % name)
          base.disableParticles()
          self._globalClock=ClockObject.getGlobalClock()
          self._globalClock.setMode(ClockObject.MSlave)
        else:
          self._frameTime=self._globalClock.getFrameTime()
          self._globalClock.setRealTime(self._frameTime)
          self._globalClock.setMode(ClockObject.MNormal)
          base.enableParticles()
          for name,id in self.agentsNamesToIDs.items():
             anAgent = self.agents[id]
             # add task for one iteration
             #taskMgr.add(anAgent.update, "updateCharacter-step-%s" % name)
          self._globalClock=None
          print "[IsisWorld] Restarting Simulator"




w = IsisWorld()

w.run()
