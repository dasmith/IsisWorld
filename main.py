#!/usr/bin/env python

"""
IsisWorld is a 3D virtual simulator for evaluating commonsense reasoning AI agents.

For more information, visit the project's website:  http://mmp.mit.edu/isisworld

IsisWorld Developers:  Dustin Smith, Chris M. Jones, Bo Morgan, Gleb Kuznetsov

"""
# Panda3D libraries:  available from http://panda3d.org
from direct.showbase import DirectObject
from panda3d.core import loadPrcFile, loadPrcFileData, ExecutionEnvironment, Filename
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task, TaskManagerGlobal
from direct.filter.CommonFilters import CommonFilters 
from direct.gui.DirectGui import DirectEntry, DirectButton
from pandac.PandaModules import * # TODO: specialize this import


#from panda3d.core import CollisionHandlerPusher, CollisionHandlerGravity, CollisionTraverser
# local source code
from src.ralphs.gravity_ralph import *
from src.physics.panda.manager import *
from src.cameras.floating import *
from src.xmlrpc.command_handler import IsisCommandHandler
from src.xmlrpc.server import XMLRPCServer
from src.loader import *
from src.lights.skydome2 import *
from time import ctime
import sys, os, threading


class IsisWorld(DirectObject.DirectObject):

    rootDirectory = Filename.fromOsSpecific(os.path.abspath(sys.path[0])).getFullpath()
    #ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")

    def __init__(self):
        # load the main simulated environment
        self.isisMessage("Starting Up")
        config = loadPrcFile(Filename(IsisWorld.rootDirectory, 'config.prc'))
        self._setupEnvironment(debug=False)
        self._setupWorld()
        self._setupAgents()
        self._setupLights()
        self._setupCameras()
        self._setupActions()
        
    def _setupEnvironment(self,debug=False):
        """  Stuff that's too ugly to put anywhere else. """
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
        commandHandler = IsisCommandHandler(self)
        # xmlrpc server
        self.server_object = XMLRPCServer()
        self.server = self.server_object.server
        self.server.register_function(commandHandler.handler,'do')
        self.server_thread = threading.Thread(group=None, target=self.server.serve_forever, name='isisworld-xmlrpc')
        self.server_thread.start()

    def _setupWorld(self):
        # setup physics
        self.physicsManager = PhysicsWorldManager()
        
        
        """ The world consists of a plane, the "ground" that stretches to infinity
        and a dome, the "sky" that sits concavely on the ground.

        For the ground component, a separate physics module must be created 
        so that the characters and objects do not fall through it.

        This is done by calling the physics module:  physicsModule.setupGround()"""
        
        self.worldObjects = {}
        base.cTrav = CollisionTraverser( ) 
        base.cTrav.showCollisions( render )        
        
        # parameters
        self.visualizeClouds = True 

    	""" The map consists of a plane, the "ground" that stretches to infinity
    	and a dome, the "sky" that sits concavely on the ground.

    	For the ground component, a separate physics module must be created 
    	so that the characters and objects do not fall through it.

    	This is done by calling the physics module:  physicsModule.setupGround()"""
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture(IsisWorld.rootDirectory+"/media/textures/env_ground.jpg")
        cm.setFrame(-100, 100, -100, 100)
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        groundNP.setTransparency(TransparencyAttrib.MAlpha)

        self.map = loader.loadModel(IsisWorld.rootDirectory+"/media/models/kitchen")
        self.map.reparentTo(render)
        self.mapNode = self.map.find("-PandaNode")
        self.room = self.mapNode.find("Wall")
        #self.worldManager.addItem(PhysicsTrimesh(name="Wall",world=self.worldManager.world, space=self.worldManager.space,pythonObject=self.room,density=800,surfaceFriction=10),False)
        self.map.node().setIntoCollideMask(BitMask32.bit(1))


        """
        Steps is yet another part of the map.
        Meant, obviously, to demonstrate the ability to climb stairs.
        """
        self.steps = self.mapNode.find("Steps")
        """
        Door functionality is also provided here.
        More on door in the appropriate file.
        """
        #self.doorNP = self.mapNode.find("Door")
        #self.door = door(self.worldManager, self.doorNP)
        #self.worldObjects['door'] = door

        #self.map.flattenStrong()
        #self.steps.flattenStrong()
        #self.doorNP.flattenStrong()


        self.worldObjects.update(load_objects(IsisWorld.rootDirectory+"/kitchen.isis", render, self.physicsManager))
        for name in self.worldObjects:
          self.worldObjects[name].flattenLight()


        """ 
        Setup the skydome
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



    def _setupCameras(self):
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


    def _setupLights(self):
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

    def _setupAgents(self):
        # agentNum keeps track of the currently active visible
        # that the camera and fov follow
        self.agentNum = 0
        self.agents = []
        self.agentsNamesToIDs = {'Ralph':0, 'Lauren':1, 'David':2}
        # add and initialize new agents
        for name in self.agentsNamesToIDs.keys():
            newAgent = Ralph(self.physicsManager, self, name, self.worldObjects)
            newAgent.control__say("Hi, I'm %s. Please build me." % name)
            self.agents.append(newAgent)
    
    def _setupActions(self):
        pass
        
    def isisMessage(self,message):
        print "[IsisWorld] %s %s" % (message, str(ctime()))

iw = IsisWorld()
run()