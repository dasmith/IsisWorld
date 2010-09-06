
import os

from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel, DirectButton, DirectOptionMenu
from direct.gui.DirectGui import DirectSlider
from direct.fsm.FSM import FSM, RequestDenied
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from pandac.PandaModules import Vec3, Vec4, PandaNode

from src.loader import *
from src.isis_scenario import *



class Controller(object, FSM):

    def __init__(self, isisworld):
        """ This configures all of the GUI states."""
        FSM.__init__(self, 'MainMenuFSM')
        # define the acceptable state transitions
        self.defaultTransitions = {
            'Menu' : ['Scenario'],
            'Scenario' : ['Menu','TaskPaused'],
            'TaskPaused' : ['Menu','TaskTrain','TaskTest','Scenario'],
            'TaskTrain' : ['TaskPaused','TaskTest','Menu','Scenario'],
            'TaskTest' : ['TaskPaused','TaskTrain','Menu','Scenario'],
        }
        self.runningSimulation = False

        self.main = isisworld
        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        self.currentScenario = None
        self.scenarioFiles = []
        self.scenarioTasks = []
        # load files in the scenario directory
        for scenarioPath in os.listdir("scenarios"):
            print "path ", scenarioPath, scenarioPath[:-3]
            if scenarioPath[-3:] == ".py":
                scenarioFile = scenarioPath[scenarioPath.rfind("/")+1:-3]
                self.scenarioFiles.append(scenarioFile)
                print "Loading scenario file", scenarioFile
                
        # display GUI for navigating tasks
        #textObj = OnscreenText(text = "Scenarios:", pos = (1,0.9), scale = 0.05,fg=(1,0.5,0.5,1),align=TextNode.ALeft,mayChange=1)
        # summer theme
        THEME = 0
        if THEME == 0:
            # summer
            FRAME_BG = (0.00,0.36,0.80,1)
            FRAME_BORDER =  (0.01, 0.01)
            POPUP_BG = (0.74,0.71,0.70,1) 
            FRAME_RELIEF = DGG.RIDGE
            BUTTON_RELIEF = DGG.RAISED
            BUTTON_BORDER = (0.02,0.02)
            BUTTON_BG = (0.74,1.00,0.94,1)
            BUTTON_FG =  (0.91,0.00,0.26,1)
            TEXT_FG = (1.00,1.00,0.27,1)
            TEXT_LARGE = (0.12,0.12)
            ALERT_TEXT_FG = (0.91,0.00,0.26,1)
        elif THEME ==1:
            FRAME_BG = (0.74,0.71,0.70,1)
            POPUP_BG = (0.54,0.45,0.47,1)
            FRAME_BORDER = (0.02, 0.02) 
            FRAME_RELIEF = DGG.RIDGE
            BUTTON_RELIEF = DGG.RAISED
            BUTTON_BORDER = (0.02,0.02)
            BUTTON_BG =  (0.29,0.09,0.18,1)
            BUTTON_FG = (1.00,0.80,0.34,1)
            TEXT_LARGE = (0.12,0.12)
            TEXT_FG =(0.02,0.19,0.25,1)
            ALERT_TEXT_FG = (0.91,0.00,0.26,1)
        #FRAME_FONT_SIZE_SMALL = 
        
        # define menu frame
        self.menuFrame = DirectFrame(frameColor=FRAME_BG,
                                     frameSize=(-1, 1, -0.75, 0.75),
                                     pos=(0, -1, 0), relief=FRAME_RELIEF,
                                     borderWidth=FRAME_BORDER)
        self.title = DirectLabel(text='IsisWorld', 
                                 relief=None,
                                 text_font=self.fonts['bold'],
                                 frameSize=(-0.5, 0.5, -0.1, 0.1),
                                 text_scale=(0.2, 0.2), pos=(0, 0, 0.45),
                                 text_fg=TEXT_FG)
        self.title.reparentTo(self.menuFrame)
        """
            Menu: When you select the scenario
            Scenario:  When you select a task
            TaskPaused:  Starting a Training or Testing session.
        
        """
        
        def setScenarioUsingGUI(arg=None):
            # you cannot do this when a task is running already
            if self.state == 'TaskPaused':
                raise Exception("FSM violation, you cannot change a task from the Task state.  First you must stop the task")
            else:
                self.selectedScenario = self.scenarioFiles[self.menuScenarioOptions.selectedIndex]


        self.menuScenarioOptions = DirectOptionMenu(text='Scenarios:',
                                                    text_font=self.fonts['normal'],
                                                    text_bg = POPUP_BG, text_fg = BUTTON_FG,
                                                    item_text_font=self.fonts['normal'], 
                                                    scale=0.1,
                                                    items=self.scenarioFiles,
                                                    textMayChange=1, 
                                                    highlightColor=(0.65,0.65,0.65,1),
                                                    command=setScenarioUsingGUI,
                                                    pos=(-.3, 0, -0.1))
        self.menuScenarioOptions.reparentTo(self.menuFrame)
        self.loadScenarioText = DirectButton(text='Load Scenario',
                                      pos=(0, 0, -.3), text_scale=TEXT_LARGE,
                                      text_font=self.fonts['bold'],borderWidth = BUTTON_BORDER,
                                      text_pos=(0, -0.01),
                                      text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                      command=self.request, extraArgs=['Scenario'])
        self.loadScenarioText.reparentTo(self.menuFrame)
        self.exitIsisWorldText = DirectButton(text='Exit', relief=BUTTON_RELIEF, borderWidth=BUTTON_BORDER,
                                     pos=(0, 0, -0.5), text_scale=TEXT_LARGE, text_bg=BUTTON_BG,
                                     text_fg=BUTTON_FG, command=self.main.exit)
        self.exitIsisWorldText.reparentTo(self.menuFrame)


        #### Define Scenario Frame
        self.scenarioFrame = DirectFrame(frameColor=FRAME_BG,
                                         frameSize=(-.33,.40,-.35,.75),
                                         pos=(.8, .2, 0), relief=FRAME_RELIEF,
                                         borderWidth=FRAME_BORDER)
                                         
        def setTaskUsingGUI(arg=None):
            # only allow this to happen if you're in the scenario state
            if not self.state == 'Scenario':
                raise Exception("FSM violation, you cannot change a task from the state %s" % self.state)
            else:
                self.selectedTask = self.currentScenario.getTaskByName(scenarioTasks[self.menuTaskOptions.selectedIndex])
                self.taskDescription.setText(str(self.selectedTask.getDescription()))

        self.menuTaskOptions = DirectOptionMenu(text="Tasks:", 
                                                text_font=self.fonts['normal'], 
                                                scale=0.06,text_bg = BUTTON_BG, text_fg = BUTTON_FG,
                                                pos=(-.25,0,.6), frameSize=(-1,1,1,1),
                                                items=self.scenarioTasks,
                                                textMayChange=1, 
                                                command=setTaskUsingGUI,
                                                highlightColor=POPUP_BG)
        self.menuTaskOptions.reparentTo(self.scenarioFrame)
        self.loadTaskText = DirectButton(text='Load Task',
                                      pos=(0, 0,.5), text_scale=(0.05),
                                      text_font=self.fonts['bold'],
                                      text_pos=(0, -0.01),borderWidth=BUTTON_BORDER,
                                      text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                      command=self.request, extraArgs=['TaskPaused'])
        self.loadTaskText.reparentTo(self.scenarioFrame)
        self.goBackFromScenarioText = DirectButton(text='Change Scenario',
                                    pos=(0,0,.3), text_scale=(0.05),
                                    text_font=self.fonts['normal'],
                                    text_pos=(0, -0.01),borderWidth=BUTTON_BORDER,
                                    text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                    command=self.request, extraArgs=['Menu'])
        self.goBackFromScenarioText.reparentTo(self.scenarioFrame)


        ### Define Task Frame
        self.taskFrame = DirectFrame(frameColor=Vec4(0,0,0,-0.3)+FRAME_BG,
                                     frameSize=(-.33,.40,-.35,.75),
                                     pos=(0.8, .2, 0), relief=FRAME_RELIEF,
                                     borderWidth=FRAME_BORDER)


        self.taskDescription = OnscreenText(text='tmp', mayChange=1, wordwrap=15,
                                         pos=(0.0, 0.6,-1), scale=(0.04),
                                         font=self.fonts['mono'],
                                         fg=TEXT_FG)
        self.taskDescription.reparentTo(self.taskFrame)
        self.toMain = DirectButton(text='Change Task',
                                   pos=(0, 0, 0), text_scale=(0.05, 0.05),borderWidth=BUTTON_BORDER,
                                   text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                   command=self.request, extraArgs=['Scenario'])
        self.toMain.reparentTo(self.taskFrame)
        self.goBackFromTaskText = DirectButton(text='Change Scenario',
                                    pos=(0,0,-.1), text_scale=(0.05),
                                    text_font=self.fonts['normal'],
                                    text_pos=(0, -0.01),borderWidth=BUTTON_BORDER,
                                    text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                    command=self.request, extraArgs=['Menu'])
        self.goBackFromTaskText.reparentTo(self.taskFrame)

        self.menuTrainButton = DirectButton(text = "Start Training", 
                                            scale=0.05, textMayChange=1, pos=(0,0,0.4),
                                            text_font=self.fonts['bold'],borderWidth=BUTTON_BORDER,
                                            text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                            command=self.request, extraArgs=['TaskTrain'])
        self.menuTestButton = DirectButton(text = "Start Testing", textMayChange=1, pos=(0,0,0.3),
                                            scale=0.05,borderWidth=BUTTON_BORDER,
                                            text_font=self.fonts['bold'],
                                            text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                            command=self.request, extraArgs=['TaskTest'])
        self.menuTrainButton.reparentTo(self.taskFrame)
        self.menuTestButton.reparentTo(self.taskFrame)
        self.request('Menu')
        

    def load_scenario_environment(self):   
        # temporary loading text
        loadingText = OnscreenText('Loading...', mayChange=True,
                                       pos=(0, -0.9), scale=0.1,
                                       fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.5))
        loadingText.setTransparency(1)
        self.main.worldNode.show()
        self.currentScenario = IsisScenario(self.selectedScenario)
        # setup world
        load_objects(self.currentScenario, self.main)
        # define pointer to base scene.
        room = render.find("**/*kitchen*").getPythonTag("isisobj")
        # position the camera in the room
        base.camera.reparentTo(room)
        base.camera.setPos(room.getWidth()/2,room.getLength()/2,room.getHeight())
        base.camera.setHpr(130,320,0)
        loadingText.destroy()
    
    def unload_scenario_environment(self):
        """ This method removes all of the objects and agents in the world, keeping only the 
        ground and sky."""
        if hasattr(self.main,'worldNode'):
            self.main.physics.destroyAllObjects()
            self.main.worldNode.removeNode()
            for agent in self.main.agents:
                agent.destroy()
        self.main.agents = []
        self.main.agentNum = 0
        self.main.agentsNamesToID = {}

    def pause_simulation(self,task=None):
        if self.runningSimulation:
            self.main.physics.stopSimulation()
            #   taskMgr.remove("visual-movingClouds")
            self.runningSimulation = False
    
    def step_simulation(self, stepTime=None):
        if not self.runningSimulation:
            if stepTime != None:
                assert stepTime >= 0.01
                # Adujust for delays to better approximate the right stopping time
                if stepTime >= .015:
                    stepTime -= .005
                taskMgr.doMethodLater(stepTime, self.pause_simulation, "physics-SimulationStopper", priority=10)
            self.runningSimulation = True
            #self.main.physics.startSimulation(stepTime)
            self.main.physics.startSimulation(1.0/40.0)

    def start_simulation(self):
        """ Starts the simulation, if it is not already running"""
        if not self.runningSimulation:
            self.step_simulation()
    
    def toggle_paused(self):
        """ Starts or Pauses the simulation, depending on the current state"""
        if self.runningSimulation:
            self.pause_simulation()
        else:
            self.start_simulation()


    def safe_request(self,newState):
        """ Attempts to advance the state and either does or returns an error message as a string instead of
        raising an exception."""
        try:
            return self.request(newState)
        except RequestDenied,e:
            return "error: request to change state denied: %s" % str(e)

    def enterMenu(self):
        self.pause_simulation()
        if hasattr(self.main,'worldNode'):
            self.main.worldNode.hide()
        taskMgr.add(self.main.cloud_moving_task, "visual-movingClouds")
        self.scenarioFrame.hide()
        # make sure default scenario is selected
        self.selectedScenario = self.scenarioFiles[self.menuScenarioOptions.selectedIndex]
        self.taskFrame.hide()
        self.menuFrame.show()


    def enterScenario(self):
        """ Loads (or resets) the current scenario. """
        #self.pause_simulation()
        self.menuFrame.hide()
        self.taskFrame.hide()

        # only initialize world if you are coming from the menu
        if self.oldState == 'Menu':
            self.unload_scenario_environment()
        
            # subnode to hang all objects on
            self.main.worldNode = base.render.attachNewNode(PandaNode('isisObjects'))
            self.load_scenario_environment()

        print "Loading from state", self.state
        # add list of tasks to the GUI
        self.scenarioTasks =  self.currentScenario.getTaskList()
        self.menuTaskOptions['items'] = self.scenarioTasks
        # oddly, you cannot initialize with a font if there are no items in the menu
        self.menuTaskOptions['item_text_font']=self.fonts['normal']
        # make sure some default task is selected
        self.selectedTask = self.currentScenario.getTaskByName(self.scenarioTasks[self.menuTaskOptions.selectedIndex])
        self.taskDescription.setText(str(self.selectedTask.getDescription()))

        self.scenarioFrame.show()
        # display options on the screen

    def enterTaskPaused(self):
        self.start_simulation()
        self.menuFrame.hide()
        self.scenarioFrame.hide()
        self.taskFrame.show()
        
    def enterTaskTrain(self):
        self.start_simulation()
        self.menuTrainButton['text'] = "Training..."
        self.menuTrainButton['state'] = DGG.DISABLED

    def exitTaskTrain(self):
        self.menuTrainButton['text'] = "Start training"
        self.menuTrainButton['state'] = DGG.NORMAL

    def enterTaskTest(self):
        self.start_simulation()
        self.menuTestButton['text']  = "Testing..."
        self.menuTestButton['state'] = DGG.DISABLED

    def exitTaskTest(self):
        self.start_simulation()
        self.menuTestButton['text'] = "Start testing"
        self.menuTestButton['state'] = DGG.NORMAL
