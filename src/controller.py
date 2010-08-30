
import os

from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel, DirectButton, DirectOptionMenu
from direct.gui.DirectGui import DirectSlider
from direct.fsm.FSM import FSM
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from pandac.PandaModules import Vec3

from src.loader import *
from src.isis_scenario import *



class Controller(object, FSM):

    def __init__(self, isisworld):
        FSM.__init__(self, 'MainMenuFSM')
        # define the acceptable state transitions
        self.defaultTransitions = {
            'Menu' : ['Scenario'],
            'Scenario' : ['Menu','TaskPaused'],
            'TaskPaused' : ['Menu','TaskTrain','TaskTest','Scenario'],
            'TaskTrain' : ['TaskPaused','TaskTest','Menu','Scenario'],
            'TaskTest' : ['TaskPaused','TaskTrain','Menu','Scenario'],
        }
        base.setBackgroundColor(0, 0, 0, 1)
        self.world = isisworld
        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        self.scenarioFiles = []
        self.scenarioTasks = []
        self._loadScenarioFiles()

        # define menu frame
        self.menuFrame = DirectFrame(frameColor=(0.32,.52,.50, 1.0),
                                     frameSize=(-1, 1, -0.75, 0.75),
                                     pos=(0, -1, 0), relief=DGG.RIDGE,
                                     borderWidth=(0.11, 0.1))
        self.title = DirectLabel(text='IsisWorld', 
                                 relief=None,
                                 text_font=self.fonts['bold'],
                                 frameSize=(-0.5, 0.5, -0.1, 0.1),
                                 text_scale=(0.2, 0.2), pos=(0, 0, 0.45),
                                 text_fg=(0.63, 0.29, 0.09, 1))
        self.title.reparentTo(self.menuFrame)
        """
            Menu: When you select the scenario
            Scenario:  When you select a task
            TaskPaused:  Starting a Training or Testing session.
        
        """
        self.menuScenarioOptions = DirectOptionMenu(text='Scenarios:',
                                                    text_font=self.fonts['normal'],  
                                                    item_text_font=self.fonts['normal'], 
                                                    scale=0.1, 
                                                    items=self.scenarioFiles,
                                                    textMayChange=1, 
                                                    highlightColor=(0.65,0.65,0.65,1),
                                                    command=self.setScenarioUsingGUI,
                                                    pos=(-.3, 0, -0.1))
        self.menuScenarioOptions.reparentTo(self.menuFrame)
        self.loadScenarioText = DirectButton(text='Load Scenario', relief=None,
                                      frameSize=(-0.2, 0.2, -0.05, 0.05),
                                      pos=(0, 0, -.3), text_scale=(0.15, 0.15),
                                      text_font=self.fonts['bold'],
                                      text_pos=(0, -0.01),
                                      text_fg=(0.63, 0.29, 0.09, 1),
                                      command=self.request, extraArgs=['Scenario'])
        self.loadScenarioText.reparentTo(self.menuFrame)
        self.exitIsisWorldText = DirectButton(text='Exit', relief=None,
                                     frameSize=(-0.2, 0.2, -0.05, 0.05),
                                     pos=(0, 0, -0.5), text_scale=(0.15, 0.15),
                                     text_fg=(0.63, 0.29, 0.09, 1), command=self.world.exit)
        self.exitIsisWorldText.reparentTo(self.menuFrame)


        #### Define Scenario Frame
        self.scenarioFrame = DirectFrame(frameColor=(0.32, 0.52, 0.50, 0.65),
                                         frameSize=(-.33,.40,-.35,.75),
                                         pos=(.8, .2, 0), relief=DGG.RIDGE,
                                         borderWidth=(0.05, 0.05))
                                         
        self.menuTaskOptions = DirectOptionMenu(text="Tasks:", 
                                                text_font=self.fonts['normal'], 
                                                scale=0.06,
                                                pos=(-.25,0,.6),
                                                items=self.scenarioTasks,
                                                textMayChange=1, 
                                                command=self.setTaskUsingGUI,
                                                highlightColor=(0.65,0.65,0.65,1))
        self.menuTaskOptions.reparentTo(self.scenarioFrame)
        self.loadTaskText = DirectButton(text='Load Task', relief=None,
                                      pos=(0, 0,.5), text_scale=(0.05),
                                      text_font=self.fonts['bold'],
                                      text_pos=(0, -0.01),
                                      text_fg=(0.63, 0.29, 0.09, 1),
                                      command=self.request, extraArgs=['TaskPaused'])
        self.loadTaskText.reparentTo(self.scenarioFrame)
        self.goBackFromScenarioText = DirectButton(text='Change Scenario', relief=None,
                                    pos=(0,0,.3), text_scale=(0.05),
                                    text_font=self.fonts['normal'],
                                    text_pos=(0, -0.01),
                                    text_fg=(0.63, 0.29, 0.09, 1),
                                    command=self.request, extraArgs=['Menu'])
        self.goBackFromScenarioText.reparentTo(self.scenarioFrame)


        ### Define Task Frame
        self.taskFrame = DirectFrame(frameColor=(0.63, 0.29, 0.09, 0.65),
                                     frameSize=(-.33,.40,-.35,.75),
                                     pos=(0.8, .2, 0), relief=DGG.RIDGE,
                                     borderWidth=(0.05, 0.05))

        self.taskNameLabel = OnscreenText(text='tmp', mayChange=1,
                                         pos=(0, 0.6,-1), scale=(0.05),
                                         font=self.fonts['mono'],
                                         fg=(0.63, 0.29, 0.09, 1))
        self.taskNameLabel.reparentTo(self.taskFrame)
        self.toMain = DirectButton(text='Change Task', relief=None,
                                   frameSize=(-0.2, 0.2, -0.05, 0.05),
                                   pos=(0, 0, 0), text_scale=(0.05, 0.05),
                                   text_fg=(0.63, 0.29, 0.09, 1),
                                   command=self.request, extraArgs=['Scenario'])
        self.toMain.reparentTo(self.taskFrame)
        self.goBackFromTaskText = DirectButton(text='Change Scenario', relief=None,
                                    pos=(0,0,-.1), text_scale=(0.05),
                                    text_font=self.fonts['normal'],
                                    text_pos=(0, -0.01),
                                    text_fg=(0.63, 0.29, 0.09, 1),
                                    command=self.request, extraArgs=['Menu'])
        self.goBackFromTaskText.reparentTo(self.taskFrame)

        self.menuTrainButton = DirectButton(text = "Start Training", 
                                            scale=0.05, relief=None, textMayChange=1,
                                            text_font=self.fonts['bold'],
                                            text_fg=(0.63, 0.29, 0.09, 1),
                                            pos=(0,0,0.4),command=self.request, extraArgs=['TaskTrain'])
        self.menuTestButton = DirectButton(text = "Start Testing", textMayChange=1,
                                            scale=0.05, relief=None,
                                            text_font=self.fonts['bold'],
                                            pos=(0,0,0.3),
                                            text_fg=(0.63, 0.29, 0.09, 1),
                                            command=self.request, extraArgs=['TaskTest'])

        self.menuTrainButton.reparentTo(self.taskFrame)
        self.menuTestButton.reparentTo(self.taskFrame)
        self.request('Menu')
        
    

    def _loadScenarioFiles(self):
        """ Loads all of the Scenario definitions from the scenario/ directory. """
        # load files in the scenario directory

        for scenarioPath in os.listdir("scenarios"):
            print "path ", scenarioPath, scenarioPath[:-3]
            if scenarioPath[-3:] == ".py":
                scenarioFile = scenarioPath[scenarioPath.rfind("/")+1:-3]
                self.scenarioFiles.append(scenarioFile)
                print "Loading scenario file", scenarioFile
                
        # display GUI for navigating tasks
        #textObj = OnscreenText(text = "Scenarios:", pos = (1,0.9), scale = 0.05,fg=(1,0.5,0.5,1),align=TextNode.ALeft,mayChange=1)
        print "Scenario Files", self.scenarioFiles




    def _setupAgents(self):
        return
        # agentNum keeps track of the currently active visible
        # that the camera and fov follow
        from random import randint
        agents_to_add = ['Ralph','Lauren']
        for agent in agents_to_add:
            newAgent = self.world.add_agent_to_world(agent)
            newAgent.actorNodePath.reparentTo(self.room)
            w,h = int(self.room.getWidth()/2), int(self.room.getLength()/2)
            x = randint(-w,w)
            y = randint(-h,h)
            newAgent.setPosition(Vec3(x,y,5))


    def setScenarioUsingGUI(self,arg=None):
        # you cannot do this when a task is running already
        if self.state == 'TaskPaused':
            raise Exception("FSM violation, you cannot change a task from the Task state.  First you must stop the task")
        else:
            self.selectedScenario = self.scenarioFiles[self.menuScenarioOptions.selectedIndex]

    def setTaskUsingGUI(self,arg=None):
        # only allow this to happen if you're in the scenario state
        if not self.state == 'Scenario':
            raise Exception("FSM violation, you cannot change a task from the state %s" % self.state)
        else:
            self.selectedTask = self.scenarioTasks[self.menuTaskOptions.selectedIndex]
            self.taskNameLabel.setText(str(self.selectedTask))

    def enterMenu(self):
        self.world.acceptAgentCommands = False
        self.scenarioFrame.hide()
        # make sure default scenario is selected
        self.selectedScenario = self.scenarioFiles[self.menuScenarioOptions.selectedIndex]
        self.taskFrame.hide()
        self.menuFrame.show()


    def _loadScene(self):   
        # temporary loading text
        loadingText = OnscreenText('Loading...', mayChange=True,
                                       pos=(0, -0.9), scale=0.1,
                                       fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.5))
        loadingText.setTransparency(1)     
        # setup world
        load_objects(self.currentScenario, self.world)
        # define pointer to base scene.
        self.room = render.find("**/*kitchen*").getPythonTag("isisobj")
        # setup agents
        self._setupAgents()
        
        # position the camera in the room
        base.camera.reparentTo(self.room)
        base.camera.setPos(self.room.getWidth()/2,self.room.getLength()/2,self.room.getHeight())
        base.camera.setHpr(130,320,0)
        loadingText.destroy()


    def enterScenario(self):
        """ Loads (or resets) the current scenario. """
        self.menuFrame.hide()
        self.taskFrame.hide()
        self.world.acceptAgentCommands = False

        # only initialize world if you are coming from the menu
        if self.oldState == 'Menu':
            if hasattr(self,'room'):
                # delete all nodes from the render path
                self.room.removeNode()
            self.world.agents = []
            self.world.agentNum = 0
            self.world.agentsNamesToID = {}
            self.currentScenario = IsisScenario(self.selectedScenario)
            self._loadScene()

        print "Loading from state", self.state
        # add list of tasks to the GUI
        self.scenarioTasks =  self.currentScenario.getTasks()
        self.menuTaskOptions['items'] = self.scenarioTasks
        # oddly, you cannot initialize with a font if there are no items in the menu
        self.menuTaskOptions['item_text_font']=self.fonts['normal']
        # make sure some default task is selected
        self.selectedTask = self.scenarioTasks[self.menuTaskOptions.selectedIndex]
        self.taskNameLabel.setText(str(self.selectedTask))

        self.scenarioFrame.show()
        # display options on the screen

    def enterTaskPaused(self):
        self.menuFrame.hide()
        self.world.acceptAgentCommands = True
        self.scenarioFrame.hide()
        self.taskFrame.show()
        
    def enterTaskTrain(self):
        self.menuTrainButton['text'] = "Training..."
        self.menuTrainButton['state'] = DGG.DISABLED

    def exitTaskTrain(self):
        self.menuTrainButton['text'] = "Start training"
        self.menuTrainButton['state'] = DGG.NORMAL

    def enterTaskTest(self):
        self.menuTestButton['text']  = "Testing..."
        self.menuTestButton['state'] = DGG.DISABLED

    def exitTaskTest(self):
        self.menuTestButton['text'] = "Start testing"
        self.menuTestButton['state'] = DGG.NORMAL
