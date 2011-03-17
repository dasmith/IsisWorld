#! /usr/bin/env python
"""
IsisWorld is a 3D virtual simulator for evaluating commonsense reasoning AI agents.

For more information, visit the project's website:  http://mmp.mit.edu/isisworld

5IsisWorld Developers:  Dustin Smith, Chris M. Jones, Bo Morgan, Gleb Kuznetsov

"""
# parameters
ISIS_VERSION = 0.5
from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", """sync-video 0
win-size 1024 768
yield-timeslice 0 
load-display pandagl 
aux-display pandadx8
client-sleep 0 
multi-sleep 0
#want-pstats 1
basic-shaders-only #f
audio-library-name null""")
# tinysdisplay, pandadx8, pandadx9
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
from src.utilities import rgb_ram_image__as__xmlrpc_image

# panda's own threading module
from direct.stdpy import threading, file
print "Threads supported?", Thread.isThreadingSupported()


class IsisWorld(DirectObject):
    physics = None
    
    def __init__(self):
        
        # TODO, read args http://www.panda3d.org/apiref.php?page=ExecutionEnvironment#getBinaryName
        # MAIN_DIR var is set in direct/showbase/DirectObject.py
        self.rootDirectory = ""#ExecutionEnvironment.getEnvironmentVariable("ISISWORLD_SCENARIO_PATH")
        for arg in xrange(ExecutionEnvironment.getNumArgs()):
            print arg, ExecutionEnvironment.getArg(arg)
        
        DirectObject.__init__(self)
        
        self.display_isis_message("Starting Up")
        
        self.current_physics_time = 0.0
        self.desired_physics_time = None # simulation unpaused (warning: must be paused while initializing IsisAgents and IsisObjects)
        self.physics_time_step    = 1.0/40.0
        
        self.rest_a_little__seconds = 1.0/30.0
        
        self.__enable_xmlrpc_vision = True
        self.__xmlrpc_port_number = 8001
        self.__display_usage_information = False
        self.__use_default_scenario = False
        self.__request_small_window = False
        self.__request_lazy_render  = False
        
        def usage():
            print "IsisWorld command line options"
            print "-"*30
            print "-h              : displays this help menu"
            print "-D              : loads first Scenario by default"
            print "-p <PORTNUMBER> : launches the XML-RPC server on the specified port. Default 8001"
            print "--small_window  : mimizes the window to 640x480"
            print "--lazy_render   : render only at 4 frames per second to use minimal CPU, useful when physics is usually paused."
            print "-"*30
        # parse command line options
        
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:vDpf", ["help", "output=", "Default", "small_window", "lazy_render"])
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            usage()
            sys.exit(2)
            
        self.verbosity = 0
        for o, a in opts:
            if o == "-v":
                self.verbosity = a
            elif o == '-f':
                print "-f option deprecated."
                #self.__enable_xmlrpc_vision = True
            elif o == '-p':
                self.__xmlrpc_port_number = a 
            elif o in ("-h", "--help"):
                self.__display_usage_information = True
            elif o in ("-D", "--default"):
                self.__use_default_scenario = True
            elif o == "--small_window":
                self.__request_small_window = True
            elif o == "--lazy_render":
                self.__request_lazy_render = True
            else:
                assert False, "unhandled option"
        
        self._setup_base_environment(debug=False)
        self._setup_lights()
        self._setup_cameras()
        self._setup_offscreen_texture()
        
        # initialize Finite State Machine to control UI
        self.controller = Controller(self, base)
        
        self._setup_actions()
        
        if self.__display_usage_information:
            usage()
            sys.exit()

        self._defaultTask = None
        if self.__use_default_scenario:
            # go to the first scenario
            self._defaultTask = a
            while not self.controller.loaded: time.sleep(0.0001)
            self.controller.request('Scenario')
            self.controller.request('TaskPaused')
        
        if self.__request_small_window:
            wp = WindowProperties()
            wp.setSize(640, 480)
            base.win.requestProperties(wp)
        
        if self.__request_lazy_render:
            self.rest_a_little__seconds = 1.0/4.0

        self._text_object_visible = True
        # turn off main help menu by default
        self._toggle_instructions_window()
        base.exitFunc = self.exit


    def make_safe_path(self,path):
        """ Working paths across different operating systems."""
        return path
        return Filename(self.rootDirectory, path)

    def reset(self):
        """ Setup the Physics manager as a class variable """ 
        IsisWorld.physics = ODEWorldManager(self)
        
        self.teacher_utterances = [] # last messages typed into dialog box
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
        
        """ Setup the skydome and moving clouds """
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
        
        self.main_window_texture = Texture("main_window-texture")
        base.win.addRenderTexture(self.main_window_texture, GraphicsOutput.RTMCopyRam)
        
        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        
        # debugging stuff
        if debug:  messenger.toggleVerbose()
        # xmlrpc server command handler
        self.commandHandler = IsisCommandHandler(self)
        self.server = XMLRPCServer(self.__xmlrpc_port_number) 
        self.server.register_function(self.commandHandler.handler,'do')
        # some hints on threading: https://www.panda3d.org/forums/viewtopic.php?t=7345
        base.taskMgr.setupTaskChain('xmlrpc',numThreads=1,frameSync=True)
        base.taskMgr.add(self.server.start_serving,  'xmlrpc-server',           taskChain='xmlrpc', priority=1000)
        base.taskMgr.add(self.run_xml_command_queue, 'xmlrpc-command-queue',    taskChain='xmlrpc', priority=1000)
        base.taskMgr.add(self.rest_a_little,         'rest-a-little',           priority=1000)
        base.taskMgr.add(self.tick_simulation_task,  'physics-step_simulation', priority=1000)
        base.taskMgr.add(self.cloud_moving_task,     'visual-movingClouds',     priority=1000)
        
        #base.taskMgr.popupControls() 
    
    def get_current_physics_time(self):
        return self.current_physics_time
    
    def cloud_moving_task(self,task):
        """ Non-essential visualization to move the clouds around."""
        self.skydomeNP.skybox.setShaderInput('time', self.current_physics_time)
        return task.cont
    
    def simulation_is_running(self):
        """ Returns True if the physics simulation is running."""
        return (self.desired_physics_time == None) or (self.current_physics_time < self.desired_physics_time - self.physics_time_step)
    
    def tick_simulation_task(self,task):
        """ this is executed in order to move the physics time to the desired physics time.""" 
        if self.simulation_is_running():
            #print "stepping simulation:", self.current_physics_time, "seconds"
            if self.desired_physics_time is None:
                self.physics.step_simulation(self.physics_time_step)
                self.current_physics_time += self.physics_time_step
            else:
                while (self.current_physics_time + self.physics_time_step < self.desired_physics_time):
                    self.physics.step_simulation(self.physics_time_step)
                    self.current_physics_time += self.physics_time_step
        return task.cont
    
    def step_simulation(self, time_step):
        """ this is used to increment the desired physics time (the tick
        function above will handle ticking actual physics time to match
        desired time)"""
        if self.desired_physics_time != None:
            self.desired_physics_time += time_step
        else:
            print "Cannot step the simulator when it is running freely"
    
    def pause_simulation(self):
        """ this is used to pause the simulation."""
        self.desired_physics_time = self.current_physics_time
    
    def resume_simulation(self):
        """ this is used to unpause the simulation (runs freely)."""
        self.desired_physics_time = None
        
    def run_xml_command_queue(self,task):
        """ Executes all of the XML-RPC commands in the queue"""
        self.commandHandler.panda3d_thread_process_command_queue()
        return task.cont
    
    def rest_a_little(self,task):
        """ Forces the rendering thread to sleep."""
        if self.rest_a_little__seconds is not None:
            time.sleep(self.rest_a_little__seconds)
        return task.cont
    
    def _setup_cameras(self):
        """" Set up displays and cameras """
        base.cam.node().setCameraMask(BitMask32.bit(0)) # show everything
        base.camera.setPos(0,0,12)
        base.camera.setP(0)
    

## offscreen rendering functions (activated with the -f command-line flag)
##
##   optimization note from bo: the offscreen texture can render only
##                              when needed, but renders constantly at
##                              the moment.  to-do after deadline.

    def _setup_offscreen_texture(self):
        if not self.__enable_xmlrpc_vision:
            return None
        fbp=FrameBufferProperties(FrameBufferProperties.getDefault())
        self.offscreen_render_buffer = base.win.makeTextureBuffer("offscreen_render-buffer", 640, 480, tex=Texture('offscreen_render-texture'), to_ram=True, fbp=fbp)
        self.offscreen_render_buffer.setActive(False)
        #self.offscreen_render_buffer.setOneShot(True)
        self.offscreen_render_texture = Texture("offscreen_render-texture")
        self.offscreen_render_buffer.addRenderTexture(self.offscreen_render_texture, GraphicsOutput.RTMCopyRam)
        self.offscreen_render_buffer.setSort(-100)
        self.offscreen_render_camera = base.makeCamera(self.offscreen_render_buffer)
        self.offscreen_render_camera.node().setCameraMask(BitMask32.bit(0)) # show everything
        self.offscreen_render_camera.node().getLens().setFov(75)
        self.offscreen_render_camera.node().getLens().setNear(0.1)
        self.offscreen_render_camera.reparentTo(base.camera)
        self.offscreen_render_camera.setPos(0, 0, 0)
        self.offscreen_render_camera.setHpr(0, 0, 0)
        print "made Texture Buffer"

    def get_offscreen_render_texture(self):
        if not self.__enable_xmlrpc_vision:
            return None
        return self.offscreen_render_texture
        
    def capture_rgb_ram_image(self):
        if not self.__enable_xmlrpc_vision:
            return None
        self.offscreen_render_buffer.setActive(True)
        base.graphicsEngine.renderFrame()
        ram_image_data = self.offscreen_render_texture.getRamImageAs('RGB')
        self.offscreen_render_buffer.setActive(False)
        if (not ram_image_data) or (ram_image_data is None):
            print 'Failed to get ram image from main window texture.'
            return None
        rgb_ram_image = {'dict_type':'rgb_ram_image', 'width':self.offscreen_render_texture.getXSize(), 'height':self.offscreen_render_texture.getYSize(), 'rgb_data':ram_image_data}
        return rgb_ram_image
    
    def capture_xmlrpc_image(self, max_x=None, max_y=None, x_offset=0, y_offset=0):
        if not self.__enable_xmlrpc_vision:
            return None
        rgb_ram_image = self.capture_rgb_ram_image()
        if rgb_ram_image is None:
            return None
        xmlrpc_image = rgb_ram_image__as__xmlrpc_image(rgb_ram_image, max_x=max_x, max_y=max_y, x_offset=x_offset, y_offset=y_offset)
        return xmlrpc_image
    
## end of offscreen rendering functions

    
    def _setup_lights(self):
        alight = AmbientLight("ambientLight")
        alight.setColor(Vec4(.7, .7, .7, 1.0))
        alightNP = render.attachNewNode(alight)
        
        dlight = DirectionalLight("directionalLight")
        dlight.setDirection(Vec3(0,0,-8))
        dlight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        dlightNP = render.attachNewNode(dlight)

        pl = PointLight("light") 
        pl.setColor(VBase4(0.5, 0.5, 0.5, 1))
        plnp=render.attachNewNode(pl) 

        render.clearLight()
        render.setShaderAuto()
        render.setLight(plnp)     
        render.setLight(alightNP)

        

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
                    self.display_isis_message("relayAgentControl: %s command not found in action controller" % (command))
                    raise self.actionController
            else:
                self.display_isis_message("Cannot relay command '%s' when there is no agent in the scenario!" % command)
            return

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
        
        #Can move with arrow keys or with w,a,s,d
        self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True,argList=['speed'],keyboardBinding="arrow_left"))
        self.actionController.addAction(IsisAction(commandName="turn_left",intervalAction=True,argList=['speed'],keyboardBinding="a"))        
        self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True,argList=['speed'],keyboardBinding="arrow_right"))
        self.actionController.addAction(IsisAction(commandName="turn_right",intervalAction=True,argList=['speed'],keyboardBinding="d"))
        self.actionController.addAction(IsisAction(commandName="move_forward",intervalAction=True,argList=['speed'],keyboardBinding="arrow_up"))
        self.actionController.addAction(IsisAction(commandName="move_forward",intervalAction=True,argList=['speed'],keyboardBinding="w"))
        self.actionController.addAction(IsisAction(commandName="move_backward",intervalAction=True,argList=['speed'],keyboardBinding="arrow_down"))
        self.actionController.addAction(IsisAction(commandName="move_backward",intervalAction=True,argList=['speed'],keyboardBinding="s"))       
        
        self.actionController.addAction(IsisAction(commandName="move_right",intervalAction=True,argList=['speed']))
        self.actionController.addAction(IsisAction(commandName="move_left",intervalAction=True,argList=['speed']))
        self.actionController.addAction(IsisAction(commandName="look_right",intervalAction=True,argList=['speed'],keyboardBinding="l"))
        self.actionController.addAction(IsisAction(commandName="look_left",intervalAction=True,argList=['speed'],keyboardBinding="h"))
        self.actionController.addAction(IsisAction(commandName="look_up",intervalAction=True,argList=['speed'],keyboardBinding="k"))
        self.actionController.addAction(IsisAction(commandName="look_down",intervalAction=True,argList=['speed'],keyboardBinding="j"))
        self.actionController.addAction(IsisAction(commandName="jump",intervalAction=False,keyboardBinding="g"))
        self.actionController.addAction(IsisAction(commandName="say",intervalAction=False,argList=['message']))
        self.actionController.addAction(IsisAction(commandName="think",intervalAction=False,argList=['message','layer']))
        self.actionController.addAction(IsisAction(commandName="sense",intervalAction=False,keyboardBinding='y'))
        self.actionController.addAction(IsisAction(commandName="sense_retina_image",intervalAction=False))
        self.actionController.addAction(IsisAction(commandName="use_aimed",intervalAction=False,keyboardBinding="u"))
        self.actionController.addAction(IsisAction(commandName="view_objects",intervalAction=False,keyboardBinding="o"))
        self.actionController.addAction(IsisAction(commandName="pick_up_with_left_hand",intervalAction=False,argList=['target'],keyboardBinding="z"))
        self.actionController.addAction(IsisAction(commandName="pick_up_with_right_hand",intervalAction=False,argList=['target'],keyboardBinding="c"))
        self.actionController.addAction(IsisAction(commandName="drop_from_left_hand",intervalAction=False,keyboardBinding="n"))
        self.actionController.addAction(IsisAction(commandName="drop_from_right_hand",intervalAction=False,keyboardBinding="m"))
        self.actionController.addAction(IsisAction(commandName="use_left_hand",intervalAction=False,argList=['target','action'],keyboardBinding="q"))
        self.actionController.addAction(IsisAction(commandName="use_right_hand",intervalAction=False,argList=['target','action'],keyboardBinding="e"))

        # initialze keybindings
        for keybinding, command in self.actionController.keyboardMap.items():
            print "adding command to ", keybinding, command
            self.accept(keybinding, relayAgentControl, [command])

        # add on-screen documentation
        self.text_objectVisible = True
        for helpString in self.actionController.helpStrings:
            text += "\n%s" % (helpString)

        props = WindowProperties( )
        props.setTitle( 'IsisWorld v%s' % ISIS_VERSION )
        base.win.requestProperties( props )

        self.text_object = OnscreenText(
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
                self.display_isis_message("Cannot switch agents because there are no agents.")
 
        # store keybindings
        self.accept("1",               base.toggleWireframe, [])
        self.accept("2",               base.toggleTexture, [])
        self.accept("3",               changeAgent, [])
        self.accept("4",               self._toggle_instructions_window, [])
        self.accept("space",           self.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("p",               self.controller.toggle_paused, [])
        #self.accept("s",               self.screenshot, ["snapshot"])
        #self.accept("a",               self.screenshot_agent, ["agent_snapshot"])
        #self.accept("d",               lambda: base.camera.setP(base.camera.getP()-1), [])
        #self.accept("f",               lambda: base.camera.setP(base.camera.getP()+1), [])
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
            print newAgent.name, agentPos
            newAgent.actorNodePath.reparentTo(room)
            if self.__enable_xmlrpc_vision:
                newAgent.initialize_retina()
            if agentPos == Vec3(0,0,0):  
                # get middle
                roomPos = room.getPos(render)
                center = room.getBounds().getCenter()
                w,h = roomPos[0]+center[0], roomPos[1]+center[1]
                newAgent.setPos(Vec3(w,h+(len(self.agents)*1),2))
            else:
                print "Position predefined for %s" % newAgent.name
        except Exception, e:
            self.display_isis_message("Could not add agent %s to room. Error: %s" % (newAgent.name, e))
        self.controller.setAgentCamera(self.agentCamera)
        return newAgent

    def _toggle_instructions_window(self):
        """ Hides the instruction window """
        if self._text_object_visible:
            self.text_object.detachNode()
            self._text_object_visible = False
        else:
            self.text_object.reparentTo(aspect2d)
            self._text_object_visible = True

    def get_all_objects_summary(self):
        objects = {}
        # find all objects with 'isisobj' tag.  Doesn't work for Python tags 
        for obj in base.render.findAllMatches("**/=isisobj"):
            o = obj.getPythonTag("isisobj")
            object_dict = {}
            object_dict['class'] = o.get_class_name()
            objects[o] = object_dict
        return objects

    def display_isis_message(self,message):
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
        sys.exit()

iw = IsisWorld()
run()
