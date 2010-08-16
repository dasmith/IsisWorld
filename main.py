#!/usr/bin/env python
"""
IsisWorld is a 3D virtual simulator for evaluating commonsense reasoning AI agents.

For more information, visit the project's website:  http://mmp.mit.edu/isisworld

IsisWorld Developers:  Dustin Smith, Chris M. Jones, Bo Morgan, Gleb Kuznetsov

"""
# parameters
ISIS_VERSION = 0.4

# Panda3D libraries:  available from http://panda3d.org
from direct.showbase.DirectObject import DirectObject
from panda3d.core import loadPrcFile, loadPrcFileData, ExecutionEnvironment, Filename
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from direct.filter.CommonFilters import CommonFilters 
from direct.fsm.FSM import FSM
from direct.gui.DirectGui import *#DirectEntry, DirectButton, DirectOptionMenu
from pandac.PandaModules import * # TODO: specialize this import

# local source code
from src.ralphs.ralph import *
from src.physics.panda.manager import *
from src.cameras.floating import *
from src.xmlrpc.command_handler import IsisCommandHandler
from src.xmlrpc.server import XMLRPCServer
from src.developerconsole import *
from src.loader import *
from src.isis_scenario import *
from src.menu import *
from src.isis_objects.layout_manager import HorizontalGridLayout
from src.lights.skydome2 import *
from src.actions.actions import *

from time import ctime
import sys, os

# panda's own threading module
from direct.stdpy import threading

from pandac.PandaModules import *
print "Threads supported?", Thread.isThreadingSupported()


class IsisWorld(DirectObject):
    def __init__(self):
        # load the main simulated environment
        
        DirectObject.__init__(self)
        self.isisMessage("Starting Up")
        # initialize Finite State Machine to control UI
        self.menu = MainMenu(self)
        self.rootDirectory = ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")
                
        self.agentNum = 0
        self.agents = []
        
        #base.config = loadPrcFile(Filename(self.rootDirectory, "config.prc"))
        self._setupEnvironment(debug=False)
        self._setupWorld(visualizeClouds=True)
        #self._setupAgents()
        self._setupLights()
        self._setupCameras()
        self._setupActions()
                  
        self._textObjectVisible = True
        #base.cTrav.showCollisions(self.objRender)
        # turn off main help menu by default
        self.toggleInstructionsWindow()
        #self.server_thread.start()
        base.exitFunc = self.exit


    def makeSafePath(self,path):
        print "In path", path, "out path", Filename(self.rootDirectory, path)
        return Filename(self.rootDirectory, path)
    
    def _setupEnvironment(self,debug=False):
        """  Stuff that's too ugly to put anywhere else. """
        base.setFrameRateMeter(True)
        base.setBackgroundColor(.2, .2, .2)
        base.camLens.setFov(75)
        base.camLens.setNear(0.1)
        base.disableMouse()
        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        
        # subnode to hang all objects on
        self.objRender = base.render.attachNewNode(PandaNode('isisObjects'))
        # debugging stuff
        if debug:
            # display all events
            messenger.toggleVerbose()
        # xmlrpc server command handler
        commandHandler = IsisCommandHandler(self)
        self.server = XMLRPCServer() 
        self.server.register_function(commandHandler.handler,'do')
        # some hints on threading: https://www.panda3d.org/forums/viewtopic.php?t=7345
        base.taskMgr.setupTaskChain('xmlrpc',numThreads=1)
        base.taskMgr.add(self.server.start_serving, 'xmlrpc-server', taskChain='xmlrpc')

    def _setupWorld(self, visualizeClouds=False):
        """ The world consists of a plane, the "ground" that stretches to infinity
        and a dome, the "sky" that sits concavely on the ground. """
         # setup physics
        self.physicsManager = PhysicsWorldManager()
        # setup ground
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture(self.makeSafePath("media/textures/env_ground.jpg"))
        cm.setFrame(-100, 100, -100, 100)
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setCollideMask(BitMask32.allOff())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        groundNP.setTransparency(TransparencyAttrib.MAlpha)
        collPlane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        floorCollisionNP = render.attachNewNode(CollisionNode('collisionNode'))
        floorCollisionNP.node().addSolid(collPlane)
        # set the bits which items can collide into
        floorCollisionNP.node().setIntoCollideMask(FLOORMASK)
        floorCollisionNP.node().setFromCollideMask(FLOORMASK)
        
        """
        Setup the skydome
        Moving clouds are pretty but computationally expensive 
        only visualize them if you have"""
        if visualizeClouds: 
            self.skydomeNP = SkyDome2(render,visualizeClouds)
            self.skydomeNP.setPos(Vec3(0,0,-500))
            self.skydomeNP.setStandardControl()
            self.skydomeNP.att_skycolor.setColor(Vec4(0.3,0.3,0.3,1))
    
            taskMgr.add(self._timeUpdated, "skytimeUpdated")
        else:
            self.skydomeNP = loader.loadModel(self.makeSafePath("media/models/dome2"))
            self.skydomeNP.reparentTo(render)
            self.skydomeNP.setCollideMask(BitMask32().allOff())
            self.skydomeNP.setScale(400, 400, 100);
    
    def _timeUpdated(self,task):
        self.skydomeNP.skybox.setShaderInput('time', task.time)
        return task.cont

    def _setupCameras(self):
        # Set up the camera 
        ### Set up displays and cameras ###
        #base.disableMouse()
        base.cam.node().setCameraMask(BitMask32.bit(0))
        base.camera.setPos(0,0,10)


    def _setupLights(self):
        alight = AmbientLight("ambientLight")
        alight.setColor(Vec4(.7, .7, .7, 1.0))
        alightNP = render.attachNewNode(alight)

        dlight = DirectionalLight("directionalLight")
        dlight.setDirection(Vec3(1, 1, -1))
        dlight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        dlightNP = render.attachNewNode(dlight)

        pl = PointLight("light") 
        plnp=render.attachNewNode(pl) 

        render.clearLight()
        render.setLight(plnp) 
        render.setShaderAuto()
        render.setLight(alightNP)
        render.setLight(dlightNP)


    def _setupActions(self):
        """ Initializes commands that are related to the XML-Server and
        the keyboard bindings """

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
        text += "\n[1] to toggle wire frame"
        text += "\n[2] to toggle texture"
        text += "\n[3] to switch agent"
        text += "\n[4] to hide/show this text"
        text += "\n[o] lists objects in agent's f.o.v."
        text += "\n[Esc] to quit\n"
        # initialize actions
        self.actionController = ActionController(0.1)
        self.actionController.addAction(IsisAction(commandName="move_left",intervalAction=True))
        self.actionController.addAction(IsisAction(commandName="move_right",intervalAction=True))
        self.actionController.addAction(IsisAction(commandName="open_fridge",intervalAction=False,keyboardBinding="p"))
        self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True,argList=['speed'],keyboardBinding="arrow_left"))
        self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True,argList=['speed'],keyboardBinding="arrow_right"))
        self.actionController.addAction(IsisAction(commandName="move_forward",intervalAction=True,argList=['speed'],keyboardBinding="arrow_up"))
        self.actionController.addAction(IsisAction(commandName="move_backward",intervalAction=True,argList=['speed'],keyboardBinding="arrow_down"))
        self.actionController.addAction(IsisAction(commandName="move_right",intervalAction=True,argList=['speed']))
        self.actionController.addAction(IsisAction(commandName="move_left",intervalAction=True,argList=['speed']))
        self.actionController.addAction(IsisAction(commandName="look_right",intervalAction=True,argList=['speed'],keyboardBinding="l"))
        self.actionController.addAction(IsisAction(commandName="look_left",intervalAction=True,argList=['speed'],keyboardBinding="h"))
        self.actionController.addAction(IsisAction(commandName="look_up",intervalAction=True,argList=['speed'],keyboardBinding="k"))
        self.actionController.addAction(IsisAction(commandName="look_down",intervalAction=True,argList=['speed'],keyboardBinding="j"))
        self.actionController.addAction(IsisAction(commandName="jump",intervalAction=False,keyboardBinding="g"))
        self.actionController.addAction(IsisAction(commandName="say",intervalAction=False,argList=['message'],keyboardBinding="t"))
        self.actionController.addAction(IsisAction(commandName="sense",intervalAction=False,keyboardBinding='y'))
        self.actionController.addAction(IsisAction(commandName="use_aimed",intervalAction=False,keyboardBinding="u"))
        self.actionController.addAction(IsisAction(commandName="view_objects",intervalAction=False,keyboardBinding="o"))
        self.actionController.addAction(IsisAction(commandName="pick_up_with_left_hand",intervalAction=False,argList=['target'],keyboardBinding="v"))
        self.actionController.addAction(IsisAction(commandName="pick_up_with_right_hand",intervalAction=False,argList=['target'],keyboardBinding="b"))
        self.actionController.addAction(IsisAction(commandName="drop_from_left_hand",intervalAction=False,keyboardBinding="n"))
        self.actionController.addAction(IsisAction(commandName="drop_from_right_hand",intervalAction=False,keyboardBinding="m"))
        self.actionController.addAction(IsisAction(commandName="use_left_hand",intervalAction=False,argList=['target','action'],keyboardBinding=","))
        self.actionController.addAction(IsisAction(commandName="use_right_hand",intervalAction=False,argList=['target','action'],keyboardBinding="."))

        # initialze keybindings
        for keybinding, command in self.actionController.keyboardMap.items():
            print "adding command to ", keybinding, command
            self.accept(keybinding, relayAgentControl, [command])

        # add on-screen documentation
        self.textObjectVisible = True
        for helpString in self.actionController.helpStrings:
            text += "\n%s" % (helpString)

        props = WindowProperties( )
        props.setTitle( 'IsisWorld v%s' % ISIS_VERSION )
        base.win.requestProperties( props )

        self.textObject = OnscreenText(
                text = text,
                fg = (.98, .9, .9, 1),
                bg = (.1, .1, .1, 0.8),
                pos = (-1.2, .9),
                scale = 0.04,
                align = TextNode.ALeft,
                wordwrap = 15,
        )

        

        def changeAgent():
            if (self.agentNum == (len(self.agents)-1)):
                self.agentNum = 0

            else:
                self.agentNum += 1
            self._setupCameras()

        # key input\\\
        self.accept("1",               base.toggleWireframe, [])
        self.accept("2",               base.toggleTexture, [])
        self.accept("3",               changeAgent, [])
        self.accept("4",               self.toggleInstructionsWindow, [])
        self.accept("space",           self.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("p",               self.physicsManager.togglePaused)
        #self.accept("r",              self.reset_simulation)
        self.accept("escape",          self.exit)

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
            message = message.strip()
            if message:
                self.agents[self.agentNum].msg = message
                self.agents[self.agentNum].control__say("Action: " + message)
            else:
                self.agents[self.agentNum].msg = None
                return
            x.teacher_utterances.append(message)
            x.command_box.enterText("")

        self.command_box = DirectEntry(pos=(-1.2,-0.95,-0.95), text_fg=(0.282, 0.725, 0.850,1), frameColor=(0.631, 0.219, 0.247,0.25), suppressKeys=1, initialText="enter text and hit return", enableEdit=0,scale=0.07, focus=0, focusInCommand=disable_keys, focusOutCommand=enable_keys, focusInExtraArgs=[self], focusOutExtraArgs=[self], command=accept_message, extraArgs=[self],  width=15, numLines=1)
        base.win.setClearColor(Vec4(0,0,0,1))

    def step_simulation(self,stepTime=2):
        """ Relays the command to the physics manager """
        self.physicsManager.stepSimulation(stepTime)

    def toggleInstructionsWindow(self):
        """ Hides the instruction window """
        if self._textObjectVisible:
            self.textObject.detachNode()
            self._textObjectVisible = False
        else:
            self.textObject.reparentTo(aspect2d)
            self._textObjectVisible = True


    def isisMessage(self,message):
        print "[IsisWorld] %s %s" % (message, str(ctime()))


    def exit(self):
        """ Shut down threads and """
        print "\n[IsisWorld] quitting IsisWorld...\n"
        if not self.physicsManager.paused:
            self.physicsManager.togglePaused()
        self.server.stop()
        #self.server_thread.join()
        sys.exit()
    
    def __exit__(self):
        self.server.stop()
        #self.server_thread.join()
        sys.exit()

iw = IsisWorld()
run()
