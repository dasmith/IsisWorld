#!/usr/bin/env python

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "sync-video 0")
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "textures-power-2 none") 
#loadPrcFileData("", "basic-shaders-only f")

from direct.showbase.ShowBase import ShowBase
from random import randint, random
import sys
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from pandac.PandaModules import *
from direct.filter.CommonFilters import CommonFilters 
from simulator.floating_camera import FloatingCamera
from direct.gui.DirectGui import DirectEntry

import simulator.skydome2 as skydome2
from simulator.odeWorldManager import *
from simulator.door import *
from simulator.ralph import *
#from simulator.david import *
from simulator.object_loader import *
from xmlrpc.xmlrpc_server import HomeSim_XMLRPC_Server
from xmlrpc.command_handler import Command_Handler
import threading

ISIS_VERSION = 0.4

        
class IsisWorld(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        base.setFrameRateMeter(True)
        base.setBackgroundColor(.2, .2, .2)
        render.setShaderAuto()
        base.camLens.setFov(75)
        base.camLens.setNear(0.2) 
        base.disableMouse()
        self.world_objects = {}
        # initialize ODE world
        self.worldManager = odeWorldManager()
        # setup components
        self.agentNum = 0
        self.setupMap()
        self.setupLights()
        self.setupAgent()
        self.setupCameras()
        self.setupControls()
        taskMgr.add(self.timeUpdated, "timeUpdated")
       
        self.paused = True

        # load objects
        self.world_objects.update(load_objects_in_world(self.worldManager,render, self.world_objects))
        # start simulation
        self.worldManager.startSimulation()
        # start server
        # xmlrpc server command handler
        xmlrpc_command_handler = Command_Handler(self)
	
        # xmlrpc server
        self.server_object = HomeSim_XMLRPC_Server()
        self.server = self.server_object.server
        self.server.register_function(xmlrpc_command_handler.command_handler,'do')
        self.server_thread = threading.Thread(group=None, target=self.server.serve_forever, name='xmlrpc')
        self.server_thread.start()


              
    def timeUpdated(self, task):
        self.skydomeNP.skybox.setShaderInput('time', task.time)
        return task.cont
 
 
    def setupMap(self):
        # GROUND
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture("textures/env_ground.jpg")
        cm.setFrame(-100, 100, -100, 100)
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        #groundNP.setAlphaScale(0.5)
        groundNP.setTransparency(TransparencyAttrib.MAlpha)
        groundGeom = OdePlaneGeom(self.worldManager.space, Vec4(0, 0, 1, 0))
        groundGeom.setCollideBits(BitMask32(0x00000021))
        groundGeom.setCategoryBits(BitMask32(0x00000012))
        groundData = odeGeomData()
        groundData.name = "ground"
        groundData.surfaceFriction = 2.0
        self.worldManager.setGeomData(groundGeom, groundData, None)

        self.skydomeNP = skydome2.SkyDome2(render)
        self.skydomeNP.setStandardControl()
        self.skydomeNP.att_skycolor.setColor(Vec4(0.3,0.3,0.3,1))
        self.skydomeNP.setPos(Vec3(0,0,-500))


        """
        Get the map's panda node. This will allow us to find the objects
        that the map consists of.
        """
        self.map = loader.loadModel("./models3/kitchen")
        self.map.reparentTo(render)
        self.mapNode = self.map.find("-PandaNode")
        self.room = self.mapNode.find("Wall")
        roomGeomData = OdeTriMeshData(self.room, True)
        roomGeom = OdeTriMeshGeom(self.worldManager.space, roomGeomData)
        roomGeom.setPosition(self.room.getPos(render))
        roomGeom.setQuaternion(self.room.getQuat(render))
        self.worldManager.setGeomData(roomGeom, groundData, False)
        """
        Add a table to the room """

        self.table = loader.loadModel("./models3/table/table")
        self.table.reparentTo(self.map)
        self.table.setPosHpr(0,2.8,0,0,0,0)
        self.table.setScale(0.007)
        
        self.world_objects['table'] = self.table
        boundingBox, offset=getOBB(self.table)

        tableGeom = OdeBoxGeom(self.worldManager.space,*boundingBox)
        tableGeom.setPosition(self.table.getPos())
        tableGeom.setQuaternion(self.table.getQuat())
        self.worldManager.setGeomData(tableGeom, groundData, False)



        """
        Steps is yet another part of the map.
        Meant, obviously, to demonstrate the ability to climb stairs.
        """
        self.steps = self.mapNode.find("Steps")
        stepsGeomData = OdeTriMeshData(self.steps, True)
        stepsGeom = OdeTriMeshGeom(self.worldManager.space, stepsGeomData)
        stepsGeom.setPosition(self.steps.getPos(render))
        stepsGeom.setQuaternion(self.steps.getQuat(render))
        self.worldManager.setGeomData(stepsGeom, groundData, None)

        """
        Door functionality is also provided here.
        More on door in the appropriate file.
        """
        self.doorNP = self.mapNode.find("Door")
        self.door = door(self.worldManager, self.doorNP)
        self.world_objects['door'] = door
        
        self.map.flattenStrong()
        self.table.flattenStrong()
        self.steps.flattenStrong()
        self.doorNP.flattenStrong()

        
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

        self.agents = []
        self.agentsNamesToIDs = {'Ralph':0, 'Lauren':1, 'David':2}
        self.agents.append(Ralph(self.worldManager, self, "Ralph"))
        self.agents[0].actor.setH(180)
        self.agents[0].setGeomPos(Vec3(-1,0,0))
        self.agents[0].control__say("Hi, I'm Ralph. Please build me.")
        
        self.agents.append(Ralph(self.worldManager, self, "Lauren"))
        self.agents[1].actor.setH(0)
        self.agents[1].setGeomPos(Vec3(-3,-3,0))
        self.agents[1].control__say("Hi, I'm Lauren. Please build me.")

        self.agents.append(Ralph(self.worldManager, self, "David"))
        self.agents[2].actor.setH(90)
        self.agents[2].setGeomPos(Vec3(3,-3,0))
        self.agents[2].control__say("Hi, I'm David. Please build me.")

        
    def setupControls(self):
        
        props = WindowProperties( )
        props.setTitle( 'IsisWorld v%s' % ISIS_VERSION )
        base.win.requestProperties( props )
        
        # TODO: re-write these instructions
        text = "\n"
        text += "IsisWorld v%s\n" % (ISIS_VERSION)
        text += "\n\n"
        text += "\nPress [i] to hide/show this text\n"
        text += "\n[o] lists objects in Ralph's f.o.v.\n"
        text += "\n[a,s,d,f] to move or zoom camera\n"
        text += "\n[Esc] to quit\n\n\n"

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

        def togglePaused():
            self.paused = not self.paused

        def changeAgent():
            if (self.agentNum == (len(self.agents)-1)):
                self.agentNum = 0
                
            else:
                self.agentNum += 1

            self.setupCameras()

        base.accept("9", changeAgent, [])

        def relayAgentControl(controlText):

            if controlText == "turn_left__start":
                self.agents[self.agentNum].control__turn_left__start()
            elif controlText == "turn_left__stop":
                self.agents[self.agentNum].control__turn_left__stop()
            elif controlText == "turn_right__start":
                self.agents[self.agentNum].control__turn_right__start()
            elif controlText == "turn_right__stop":
                self.agents[self.agentNum].control__turn_right__stop()
            elif controlText == "move_forward__start":
                self.agents[self.agentNum].control__move_forward__start()
            elif controlText == "move_forward__stop":
                self.agents[self.agentNum].control__move_forward__stop()
            elif controlText == "move_backward__start":
                self.agents[self.agentNum].control__move_backward__start()
            elif controlText == "move_backward__stop":
                self.agents[self.agentNum].control__move_backward__stop()
            elif controlText == "look_up__start":
                self.agents[self.agentNum].control__look_up__start()
            elif controlText == "look_up__stop":
                self.agents[self.agentNum].control__look_up__stop()
            elif controlText == "look_down__start":
                self.agents[self.agentNum].control__look_down__start()
            elif controlText == "look_down__stop":
                self.agents[self.agentNum].control__look_down__stop()
            elif controlText == "look_left__start":
                self.agents[self.agentNum].control__look_left__start()
            elif controlText == "look_left__stop":
                self.agents[self.agentNum].control__look_left__stop()
            elif controlText == "look_right__start":
                self.agents[self.agentNum].control__look_right__start()
            elif controlText == "look_right__stop":
                self.agents[self.agentNum].control__look_right__stop()
            elif controlText == "jump":
                self.agents[self.agentNum].control__jump()
            elif controlText == "use_aimed":
                self.agents[self.agentNum].control__use_aimed()
                    
        
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
        base.accept("arrow_left",     relayAgentControl, ["turn_left__start"])
        base.accept("arrow_left-up",  relayAgentControl, ["turn_left__stop"])
        base.accept("arrow_right",    relayAgentControl, ["turn_right__start"])
        base.accept("arrow_right-up", relayAgentControl, ["turn_right__stop"])
        base.accept("arrow_up",       relayAgentControl, ["move_forward__start"])
        base.accept("arrow_up-up",    relayAgentControl, ["move_forward__stop"])
        base.accept("arrow_down",     relayAgentControl, ["move_backward__start"])
        base.accept("arrow_down-up",  relayAgentControl, ["move_backward__stop"])
        # head movement controls (vi direction map)
        base.accept("k",              relayAgentControl, ["look_up__start"])
        base.accept("k-up",           relayAgentControl, ["look_up__stop"])
        base.accept("j",              relayAgentControl, ["look_down__start"])
        base.accept("j-up",           relayAgentControl, ["look_down__stop"])
        base.accept("h",              relayAgentControl, ["look_left__start"])
        base.accept("h-up",           relayAgentControl, ["look_left__stop"])
        base.accept("l",              relayAgentControl, ["look_right__start"])
        base.accept("l-up",           relayAgentControl, ["look_right__stop"])
        # atomic actions
        base.accept("space",          relayAgentControl, ["jump"])
        base.accept("u",              relayAgentControl, ["use_aimed"])

         

        base.accept("i", hideText)

        # key input
        self.accept("space",           self.step_simulation, [.1]) # argument is amount of second to advance
        self.accept("o",               self.printObjects, []) # displays objects in field of view
        self.accept("p",               togglePaused)
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

    def step_simulation(self,time=5):
        pass


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

def detonate():
    explosion(w.worldManager, Vec3(0, 0, 0))

#base.accept("b", detonate)

w.run()
