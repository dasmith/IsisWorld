#! /usr/bin/env python
"""
IsisWorld is a 3D virtual simulator for evaluating commonsense reasoning AI agents.

For more information, visit the project's website:  http://mmp.mit.edu/isisworld

IsisWorld Developers:  Dustin Smith, Chris M. Jones, Bo Morgan, Gleb Kuznetsov

"""
# parameters
ISIS_VERSION = 0.4
from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", """sync-video 0
win-size 1024 768
yield-timeslice 0 
client-sleep 0 
multi-sleep 0
basic-shaders-only #f
audio-library-name null""")

import time
import sys
import os
import getopt

# Panda3D libraries:  available from http://panda3d.org
from panda3d.core import ExecutionEnvironment, Filename
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from direct.filter.CommonFilters import CommonFilters 
from direct.fsm.FSM import FSM
from pandac.PandaModules import * # TODO: specialize this import
from direct.showbase.DirectObject import DirectObject

# local source code
from src.physics.ode.odeWorldManager import *
from src.cameras.floating import *
from src.xmlrpc.command_handler import IsisCommandHandler
from src.xmlrpc.server import XMLRPCServer
from src.developerconsole import *
from src.loader import *
from src.isis_scenario import *
from src.controller import *
from src.isis_objects.layout_manager import HorizontalGridLayout
from src.lights.skydome2 import *
from src.actions.actions import *

# panda's own threading module
from direct.stdpy import threading, file

print "Threads supported?", Thread.isThreadingSupported()


class IsisWorld(DirectObject):
    physics = None
    
    def __init__(self):
        # MAIN_DIR var is set in direct/showbase/ShowBase.py
        self.rootDirectory = ExecutionEnvironment.getEnvironmentVariable("ISISWORLD_SCENARIO_PATH")
        
        DirectObject.__init__(self)

        self.isisMessage("Starting Up")
        
        self._setup_base_environment(debug=False)
        self._setup_lights()
        self._setup_cameras()

        # initialize Finite State Machine to control UI
        self.controller = Controller(self)
        
        self._setup_actions()
        
        # parse command line options
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:vD", ["help", "output=","Default"])
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            usage()
            sys.exit(2)
            
        self.verbosity = 0
        self._defaultTask = None
        for o, a in opts:
            if o == "-v":
                self.verbosity = a
            elif o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("-D", "--default"):
                # go to the first scenario
                self._defaultTask = a
                while not self.controller.loaded: time.sleep(0.0001)
                self.controller.request('Scenario')
                self.controller.request('TaskPaused')
            else:
                assert False, "unhandled option"
        
        self._textObjectVisible = True
        # turn off main help menu by default
        self.toggleInstructionsWindow()
        base.exitFunc = self.exit


    def make_safe_path(self,path):
        """ Working paths across different operating systems."""
        return path
        return Filename(self.rootDirectory, path)

    def reset(self):
        print "RESET MAIN CALLED\n\n"
        """ Setup the Physics manager as a class variable """ 
        IsisWorld.physics = ODEWorldManager(self)
        
        self.teacher_utterances = [] # last message typed
        # main dialogue box
        self.agents = []
        self.agentNum = 0
        self.agentsNamesToIDs = {}
        self.objects = []
        self.worldNode = base.render.attachNewNode(PandaNode('isisObjects'))

        """ The world consists of a plane, the "ground" that stretches to infinity
        and a dome, the "sky" that sits concavely on the ground. """
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture(self.make_safe_path("media/textures/env_ground.jpg"))
        cm.setFrame(-100, 100, -100, 100)
        groundNP = self.worldNode.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        groundNP.setTransparency(TransparencyAttrib.MAlpha)
        
        obj = staticObject(self)
        obj.geom =  OdePlaneGeom(IsisWorld.physics.space, Vec4(0, 0, 1, 0))
        obj.setCatColBits("environment")
        IsisWorld.physics.addObject(obj)
        
        """ Setup the skydome
        Moving clouds are pretty but computationally expensive """
        self.skydomeNP = SkyDome2(self.worldNode,True)
        self.skydomeNP.setPos(Vec3(0,0,-500))
        self.skydomeNP.setStandardControl()
        self.skydomeNP.att_skycolor.setColor(Vec4(0.3,0.3,0.3,1))

    def _setup_base_environment(self,debug=False):
        """  Configuration code for basic window management, and the XML-RPC server.
        Everything here is only loaded ONCE."""
       
        base.setFrameRateMeter(True)
        base.setBackgroundColor(.2, .2, .2)
        base.camLens.setFov(75)
        base.camLens.setNear(0.1)
        base.disableMouse()
        
        base.graphicsEngine.renderFrame()
        base.graphicsEngine.renderFrame()

        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        
        # debugging stuff
        if debug:  messenger.toggleVerbose()
        # xmlrpc server command handler
        self.commandHandler = IsisCommandHandler(self)
        self.server = XMLRPCServer() 
        self.server.register_function(self.commandHandler.handler,'do')
        # some hints on threading: https://www.panda3d.org/forums/viewtopic.php?t=7345
        base.taskMgr.setupTaskChain('xmlrpc',numThreads=1)
        base.taskMgr.add(self.server.start_serving, 'xmlrpc-server', taskChain='xmlrpc')
        base.taskMgr.add(self.run_xml_command_queue,'xmlrpc-command-queue', priority=1000)
        
    
    def cloud_moving_task(self,task):
        """ Non-essential visualization to move the clouds around."""
        self.skydomeNP.skybox.setShaderInput('time', task.time)
        return task.cont
    
    def run_xml_command_queue(self,task):
        self.commandHandler.panda3d_thread_process_command_queue()
        return task.cont

    def _setup_cameras(self):
        # Set up the camera 
        ### Set up displays and cameras ###
        base.cam.node().setCameraMask(BitMask32.bit(0))
        base.camera.setPos(0,0,12)
        base.camera.setP(0)#315)


    def _setup_lights(self):
        alight = AmbientLight("ambientLight")
        alight.setColor(Vec4(.7, .7, .7, 1.0))
        alightNP = render.attachNewNode(alight)

        #dlight = DirectionalLight("directionalLight")
        #dlight.setDirection(Vec3(self.worldNode.getHpr()))
        #dlight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        #dlightNP = render.attachNewNode(dlight)

        pl = PointLight("light") 
        pl.setColor(VBase4(0.2, 0.2, 0.2, 1))
        plnp=render.attachNewNode(pl) 

        render.clearLight()
        render.setShaderAuto()
        render.setLight(plnp)     
        render.setLight(alightNP)
        #render.setLight(dlightNP)
        


    def _setup_actions(self):
        """ Initializes commands that are related to the XML-Server and
        the keyboard bindings """

        def relayAgentControl(command):
            """ Accepts an instruction issued through the bound keyboard commands
            because "self.agentNum" need to be revaluated at the time the command
            is issued, necessitating this helper function"""
            if  len(self.agents) > 0: 
                if self.actionController.hasAction(command):
                    self.actionController.makeAgentDo(self.agents[self.agentNum], command)
                else:
                    self.isisMessage("relayAgentControl: %s command not found in action controller" % (command))
                    raise self.actionController
            else:
                self.isisMessage("Cannot relay command '%s' when there is no agent in the scenario!" % command) 

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
            if len(self.agents) > 0:
                if (self.agentNum == (len(self.agents)-1)):
                    self.agentNum = 0
                else:
                    self.agentNum += 1
                # change agent view camera
                self.agentCamera.setCamera(self.agents[self.agentNum].fov)
            else:
                self.isisMessage("Cannot switch agents because there are no agents.")
 
        # store keybindings
        self.accept("1",               base.toggleWireframe, [])
        self.accept("2",               base.toggleTexture, [])
        self.accept("3",               changeAgent, [])
        self.accept("4",               self.toggleInstructionsWindow, [])
        self.accept("space",           self.controller.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("p",               self.controller.toggle_paused)
        self.accept("s",               self.screenshot, ["snapshot"])
        self.accept("a",               self.screenshot_agent, ["agent_snapshot"])
        self.accept("escape",          self.exit)



        base.win.setClearColor(Vec4(0,0,0,1))


    def add_agent_to_world(self, newAgent): 
        # add and initialize new agents
        newAgent.control__say("Hi, I'm %s. Please build me." % newAgent.name)
        self.agents.append(newAgent)
        self.agentsNamesToIDs[newAgent.name] = len(self.agents)-1
        #self.agents.sort(key=lambda x:self.agentsNamesToIDs[x.name])
        
        # set up picture in picture on first agent
        if len(self.agents) == 1:
            dr = base.camNode.getDisplayRegion(0)
            aspect_ratio = 16.0 / 9.0
            window = dr.getWindow()
            pip_size = 0.40 # percentage of width of screen
            self.agentCamera = window.makeDisplayRegion(1-pip_size,1,0,\
                 (1.0 / aspect_ratio) * float(dr.getPixelWidth())/float(dr.getPixelHeight()) * pip_size)    
        
            self.agentCamera.setSort(dr.getSort())
            self.agentCamera.setClearColor(VBase4(0, 0, 0, 1))
            self.agentCamera.setClearColorActive(True)
            self.agentCamera.setClearDepthActive(True)
            self.agentCamera.setCamera(self.agents[self.agentNum].fov)
            self.agentCamera.setActive(1)
        # position the agent randomly
        try: 
            room = render.find("**/*kitchen*").getPythonTag("isisobj")
            agentPos = newAgent.actorNodePath.getPos(render)
            newAgent.actorNodePath.reparentTo(room)
            if agentPos == Vec3(0,0,0):  
                # get middle
                roomPos = room.getPos(render)
                center = room.getBounds().getCenter()
                w,h = roomPos[0]+center[0], roomPos[1]+center[1]
                newAgent.setPos(Vec3(w,h+(len(self.agents)*0.5),5))
            else:
                agentPos[2] = 5
                newAgent.setPos(agentPos)
        except Exception, e:
            self.isisMessage("Could not add agent %s to room. Error: %s" % (newAgent.name, e))
        return newAgent

    def toggleInstructionsWindow(self):
        """ Hides the instruction window """
        if self._textObjectVisible:
            self.textObject.detachNode()
            self._textObjectVisible = False
        else:
            self.textObject.reparentTo(aspect2d)
            self._textObjectVisible = True


    def isisMessage(self,message):
        print "[IsisWorld] %s %s" % (message, str(time.ctime()))

    def screenshot(self, name):
        name = os.path.join("screenshots", name+"_")
        num = 0
        while os.path.exists(name+str(num)+".jpg"):
            num += 1
        base.camNode.getDisplayRegion(0).saveScreenshot(name+str(num)+".jpg")

    def screenshot_agent(self, name):
        name = os.path.join("screenshots", name+"_")
        num = 0
        while os.path.exists(name+str(num)+".jpg"):
            num += 1
        self.agentCamera.saveScreenshot(name+str(num)+".jpg")

    def exit(self):
        """ Shut down threads and """
        print "\n[IsisWorld] quitting IsisWorld...\n"
        self.__exit__()
    
    def __exit__(self):
        self.server.stop()
        #self.server_thread.join()
        sys.exit()

iw = IsisWorld()
run()

