
import os
import operator
import imp
import struct

from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel, DirectButton, DirectOptionMenu, DirectEntry
from direct.gui.DirectGui import DirectSlider, RetryCancelDialog, DirectCheckButton
from direct.fsm.FSM import FSM, RequestDenied
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.stdpy import threading, file
from panda3d.core import ExecutionEnvironment, Filename
from pandac.PandaModules import Vec3, Vec4, PandaNode, PNMImage, HTTPClient, Ramfile, DocumentSpec

from src.isis_scenario import *
from utilities import pnm_image__as__xmlrpc_image

class Controller(object, FSM):

    def __init__(self, isisworld, base):
        """ This configures all of the GUI states."""
        self.loaded = True
        self.base = base
        FSM.__init__(self, 'MainMenuFSM')
        # define the acceptable state transitions
        self.defaultTransitions = {
            'Menu' : ['Scenario'],
            'Scenario' : ['Menu','TaskPaused', 'ScenarioLoadError'],
            'ScenarioLoadError' : ['Menu', 'Scenario'],
            'TaskPaused' : ['Menu','TaskTrain','TaskTest','Scenario'],
            'TaskTrain' : ['TaskPaused','TaskTest','Menu','Scenario'],
            'TaskTest' : ['TaskPaused','TaskTrain','Menu','Scenario'],
        }
        
        #Convenience fields.
        self.taskBarShown = False
        self.scenarioBarShown = True
        
        self.main = isisworld
        # load a nicer font
        self.fonts = {'bold': base.loader.loadFont('media/fonts/DroidSans-Bold.ttf'), \
                       'mono': base.loader.loadFont('media/fonts/DroidSansMono.ttf'),\
                       'normal': base.loader.loadFont('media/fonts/DroidSans.ttf')}
        self.currentScenario = None
        self.scenarioFiles = []
        self.scenarioTasks = []
        
        
        # load files in the scenario directory
        print "LOADING SCENARIO FILES", self.main.rootDirectory
        for scenarioPath in os.listdir(self.main.rootDirectory+"scenarios"):
            scenarioFile = scenarioPath[scenarioPath.rfind("/")+1:]
            if "__init__" not in scenarioFile:
                self.scenarioFiles.append(scenarioFile)
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
            BUTTON_RELIEF = DGG.FLAT
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
            BUTTON_RELIEF = DGG.FLAT
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

        #                                            item_text_font=self.fonts['normal'], 
        self.menuScenarioOptions = DirectOptionMenu(text='Scenarios:',
                                                    text_font=self.fonts['normal'],
                                                    text_bg = POPUP_BG, text_fg = BUTTON_FG,
                                                    scale=0.1,
                                                    items=self.scenarioFiles,
                                                    textMayChange=1, 
                                                    highlightColor=(0.65,0.65,0.65,1),
                                                    command=setScenarioUsingGUI,
                                                    pos=(-.3, 0, -0.1),
                                                    frameSize = (-.8, -.6, -.3, .3))
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
                                         pos=(0.0, 0.7), scale=(0.04),
                                         font=self.fonts['mono'],
                                         fg=TEXT_FG)
        self.taskDescription.reparentTo(self.taskFrame)
        self.toMenu = DirectButton(text='Change Task', pos=(0.0, 0.0, 0.3), text_scale=(0.05, 0.05),borderWidth=BUTTON_BORDER,
                                   text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                   command=self.request, extraArgs=['Scenario'])
        self.toMenu.reparentTo(self.taskFrame)
        self.goBackFromTaskText = DirectButton(text='Change Scenario',
                                    pos=(0,0,0.2), text_scale=(0.05),
                                    text_font=self.fonts['normal'],
                                    text_pos=(0, -0.01),borderWidth=BUTTON_BORDER,
                                    text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                    command=self.request, extraArgs=['Menu'])
        self.goBackFromTaskText.reparentTo(self.taskFrame)

        #Add a toolbar
        self.toolbarFrame = DirectFrame(frameColor=Vec4(0, 0, 0, -0.3) + FRAME_BG,
                                        frameSize = (-1.4, 0.8, 0.86, 1.0),
                                        pos=(.07, 0, -.008), relief=FRAME_RELIEF,
                                        borderWidth=FRAME_BORDER)
        #Add button to take a screenshot
        self.screenShotButton = DirectButton(text='Take Screenshot', pos=(-1.15, 0, .92), text_scale=(0.05, 0.05),
                                             borderWidth=BUTTON_BORDER,
                                               text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                            command = self.screenshot, extraArgs=['snapshot'])
        self.screenShotButton.reparentTo(self.toolbarFrame)
        
        #Add a button to take an agent screenshot
        self.getAgentScreenshot = DirectButton(text = 'Agent Screenshot', pos = (-.7, 0 ,.92),text_scale=(0.05, 0.05),
                                            borderWidth = BUTTON_BORDER,
                                              text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                              command = self.screenshot_agent, extraArgs=['agent_snapshot'])
        self.getAgentScreenshot.reparentTo(self.toolbarFrame);
        
        #Add a button to move camera up
        self.upCamera = DirectButton(text = '+', pos = (-.4, 0, .92), text_scale = (0.05, 0.05),
                                     borderWidth = BUTTON_BORDER,
                                    text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                    command = lambda: base.camera.setP(base.camera.getP()+1))
        self.upCamera.reparentTo(self.toolbarFrame)
        
        #Add button to move camera down
        self.downCamera = DirectButton(text = '-', pos = (-.3, 0, .92), text_scale = (0.05, 0.05),
                                     borderWidth = BUTTON_BORDER,
                                    text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                    command = lambda: base.camera.setP(base.camera.getP()-1))
        self.downCamera.reparentTo(self.toolbarFrame)

        #Pause button
        self.pauseButton = DirectButton(text = 'Pause', pos=(-0.10, 0, .92), text_scale=(0.05, 0.05),
                                            borderWidth = BUTTON_BORDER,
                                              text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                           command = self.toggle_paused)
        self.pauseButton.reparentTo(self.toolbarFrame)

        self.unpauseButton = DirectButton(text = 'Unpause', pos=(-0.10, 0, .92), text_scale=(0.05, 0.05),
                                            borderWidth = BUTTON_BORDER,
                                              text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                           command = self.toggle_paused)
        self.unpauseButton.reparentTo(self.toolbarFrame)
        self.unpauseButton.hide()

        #Button to toggle task frames
        self.scenarioBarControl = DirectButton(text = 'Toggle Scenario Options', pos=(0.35, 0, .92), text_scale=(0.05, 0.05),
                                            borderWidth = BUTTON_BORDER,
                                              text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                           command = self.scenarioBarControlPress)

        self.taskBarControl = DirectButton(text = 'Toggle Taskbar', pos=(.35, 0, .92), text_scale=(0.05, 0.05),
                                            borderWidth = BUTTON_BORDER,
                                              text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                           command = self.taskBarControlPress)
        
        self.scenarioBarControl.reparentTo(self.toolbarFrame)
        self.taskBarControl.reparentTo(self.toolbarFrame)                                       
        self.taskBarControl.hide()
        self.scenarioBarControl.hide()

        def click_test_button():
            if self.state == 'TaskTest':
                self.request('TaskPaused')
            else:
                self.request('TaskTest')

        def click_reset_button():
            if self.state == 'TaskTrain':
                self.request('TaskPaused')
            else:
                self.request('TaskTrain')
    
        self.menuResetTrainingButton = DirectButton(text = "Reset Task", 
                                            scale=0.05, textMayChange=1, pos=(0,0,0.4),
                                            text_font=self.fonts['bold'],borderWidth=BUTTON_BORDER,
                                            text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                            command=click_reset_button)
        self.menuTestButton = DirectButton(text = "Start Testing", textMayChange=1, pos=(0,0,0.5),
                                            scale=0.05,borderWidth=BUTTON_BORDER,
                                            text_font=self.fonts['bold'],
                                            text_fg=BUTTON_FG, text_bg = BUTTON_BG, relief=BUTTON_RELIEF,
                                            command=click_test_button)
        self.menuResetTrainingButton.hide()
        self.menuResetTrainingButton.reparentTo(self.taskFrame)
        self.menuTestButton.reparentTo(self.taskFrame)
        

        def disable_keys(x):
            x.testCommandBox.enterText("")
            x.testCommandBox.suppressKeys=True
            x.testCommandBox["frameColor"]=(0.631, 0.219, 0.247,1)

        def enable_keys(x):
            x.testCommandBox["frameColor"]=(0.631, 0.219, 0.247,.25)
            x.testCommandBox.suppressKeys=False

        def accept_message(message,x):
            message = message.strip()
            if len(message.split()) > 1 and message.split()[0] == 'do':
                if len(message.split()) > 2 and message.split()[1] == "right":
                    self.main.agents[self.main.agentNum].control__use_right_hand(None," ".join(message.split()[2:]))
                elif len(message.split()) > 2 and message.split()[1] == "left":
                    self.main.agents[self.main.agentNum].control__use_left_hand(None," ".join(message.split()[2:]))
                else:
                    # by default, when no hand is mentioned, use right hand
                    self.main.agents[self.main.agentNum].control__use_right_hand(None," ".join(message.split()[1:]))
            else:
                self.main.agents[self.main.agentNum].msg = message
                self.main.agents[self.main.agentNum].control__say("Action: " + message)
                return
            x.main.teacher_utterances.append(message)
            x.testCommandBox.enterText("")

        self.testCommandBox = DirectEntry(pos=(-1.2,-0.95,-0.95), text_fg=(0.282, 0.725, 0.850,1), frameColor=(0.631, 0.219, 0.247,0.25),
                                          suppressKeys=1, initialText="enter text and hit return", enableEdit=0,scale=0.07, focus=0,
                                          focusInCommand=disable_keys, focusOutCommand=enable_keys, focusInExtraArgs=[self],
                                          focusOutExtraArgs=[self], command=accept_message, extraArgs=[self],  width=15, numLines=1)
        
        self.testCommandBox.reparentTo(self.toolbarFrame)
        self.loaded = True
        
        self.thought_buttons = {}
        self.thought_filter = []
        self.setup_thought_filters({0: {'name': 'Reactive'}, 1:{'name':'Deliberative'}, 2: {'name':'Reflective'}})

        self.request('Menu')

    def _censorAgents(self):
        """ Updates the kinds of thoughts that the agents display. """
        if hasattr(self.main,'agents'):
            for agent in self.main.agents:
                agent.thought_filter = dict(map(lambda x: (x,self.thought_buttons[x].component('text0').textNode.getFrameColor()),self.thought_filter))
        


    def setup_thought_filters(self, config):
        """ This functions sets up the GUI which can be used to display the 
        agents' thoughts. It is given a dictionary of """
        
        # first disable old ones:
        for button in self.thought_buttons.values():
            button.destroy()
        # reset old thought buttons
        self.thought_buttons = {}
        self.thought_filter = []
        # go through the keys in the first one, sorted by the key values, which
        # should be numeric.
        offset = 0.1
        
        def update_thought_filter_checkbox(checked):
            self.thought_filter = []
            for key, button in self.thought_buttons.items():
                if button["indicatorValue"]:
                    self.thought_filter.append(key)
            # update agents
            self._censorAgents()
        
        for key, opts in sorted(config.iteritems(), key=operator.itemgetter(0)):
            # extract name:
            if opts.has_key('name'):
                name = opts['name']
            else:
                name = 'Layer %s' % key
            
            # extract color
            if opts.has_key('color') and len(opts['color']) == 4:
                color = opts['color']
            else:
                color = (0.1,0.1,0.1,1)
                
            # extract default state
            if opts.has_key('checked'):
                checked = opts['checked']
            else:
                checked = True
            
            if checked: 
                self.thought_filter.append(key)
            
            newButton = DirectCheckButton(text = name,
                                          scale=0.05, 
                                          textMayChange=1,
                                          indicatorValue = checked,
                                          pos=(0,0,.1-offset),
                                          text_font=self.fonts['normal'],
                                          borderWidth=(0.02,0.02),
                                          text_fg=color,
                                          text_bg =(0.74,1.00,0.94,1),
                                          relief=DGG.RAISED,
                                          command=update_thought_filter_checkbox)
            newButton.reparentTo(self.taskFrame)
            offset += 0.1
            # add to list
            self.thought_buttons[key] = newButton
            
        # update the agents
        self._censorAgents()
        return True
        
    def pause_simulation(self,task=None):
        if self.main:
            #self.main.physics.stopSimulation()
            self.main.pause_simulation()
            
    def step_simulation(self, step_time):
        self.main.step_simulation(step_time)

    def start_simulation(self):
        """ Starts the simulation, if it is not already running"""
        if not self.main.simulation_is_running():
            self.main.resume_simulation()
    
    def toggle_paused(self):
        """ Starts or Pauses the simulation, depending on the current state"""
        if self.main.simulation_is_running():
            self.pause_simulation()
            self.pauseButton.hide()
            self.unpauseButton.show()
        else:
            self.start_simulation()
            self.unpauseButton.hide()
            self.pauseButton.show()

    def reset_scenario(self):
        """ Resets the scenario if one is already running"""
        if self.state in ['Scenario','TaskTrain','TaskPaused','TaskTest']:
            self.pause_simulation()
            self.request('Menu')
            return self.request('Scenario')
        else:
            return "error: cannot reset unless you have a scenario loaded."
            
    def safe_request(self,newState):
        """ Attempts to advance the state and either does or returns an error message as a string instead of
        raising an exception."""
        try:
            return self.request(newState)
        except RequestDenied,e:
            return "error: request to change state denied: %s" % str(e)

    def enterMenu(self):
        self.taskFrame.hide()
        self.taskBarControl.hide()
        self.scenarioBarControl.hide()
        self.scenarioFrame.hide()
        self.toolbarFrame.hide()
        self.pause_simulation()
        
        # unload the previous scene if it's there
        if hasattr(self.main,'worldNode'):
            del self.currentScenario
            self.currentScenario = None
            # kitchen 
            for obj in self.main.objects:
                obj.remove_from_world()
            for agent in self.main.agents:
                agent.destroy()
            self.main.physics.destroy() 
            self.main.worldNode.removeNode()
        self.main.reset()
        
        # start the moving clouds
        taskMgr.add(self.main.cloud_moving_task, "visual-movingClouds")
        
        # reveal the correct GUI
        self.menuFrame.show()

        # make sure default scenario is selected
        self.selectedScenario = self.scenarioFiles[self.menuScenarioOptions.selectedIndex]

    def exitMenu(self):
        self.menuFrame.hide()

    def enterScenario(self):
        """ Loads (or resets) the current scenario. """
        loadingText = OnscreenText('Loading...', mayChange=True,
                                       pos=(0, -0.9), scale=0.1,
                                       fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.5))
        loadingText.setTransparency(1)
        if self.oldState in ['Menu']:
            # reload the scenario

            def parsingProblemDialogCallback(arg):
                if arg == 1: 
                    self.request('Scenario')
                else: # cancel
                    self.request('Menu')
                dialogbox.cleanup()
            
            try:
                print "Selected Scenario", self.selectedScenario
                #os.chdir(self.main.rootDirectory+"scenarios")
                #print sys.path[0] 
                #print os.getcwd()
                print "NAME", self.selectedScenario[:-3]
                print "OPENING", "scenarios/"+self.selectedScenario
                if self.selectedScenario.lower()[-3:] == '.py':
                    py_mod = imp.load_source(self.selectedScenario[:-3], "scenarios/"+self.selectedScenario)
                elif self.selectedScenario.lower()[-4:] == '.pyo':
                    # these files are loaded within the packaged P3D files
                    import marshal
                    def loadPYbyte(path): 
                        # read module file 
                        marshal_data= VFS.readFile(Filename(path),1)[8:] 
                        # unmarshal the data 
                        return marshal.loads(marshal_data)
                    py_mod = imp.load_compiled(self.selectedScenario[:-4], loadPYbyte(self.selectedScenario))
                else:
                    raise Exception("Invalid file extension for %s " % (self.selectedScenario))
                if 'Scenario' in dir(py_mod):
                    self.currentScenario = py_mod.Scenario(self.selectedScenario) 
                    
                print "Current scenario methods", dir(self.currentScenario)
                # setup world
                self.main.pause_simulation()
                self.currentScenario.loadScenario(self.main)
            except IsisParseProblem as e:
                dialogbox = RetryCancelDialog(text='There was a problem parsing the scenario file\
                                  : \n %s.  \n\nLocation %s' % (e.message, e.component),\
                                 command=parsingProblemDialogCallback)
            else:
                # define pointer to base scene.
                room = render.find("**/*kitchen*").getPythonTag("isisobj")
                # position the camera in the room
                base.camera.reparentTo(room)
                base.camera.setPos(room.getWidth()/4,room.getLength()/4,room.getHeight()*3/4)
                base.camera.setHpr(145,-30,0)
                # add list of tasks to the GUI
                self.scenarioTasks =  self.currentScenario.getTaskList()
                self.menuTaskOptions['items'] = self.scenarioTasks
                # oddly, you cannot initialize with a font if there are no items in the menu
                # self.menuTaskOptions['item_text_font']=self.fonts['normal']
                # make sure some default task is selected
                self.selectedTask = self.currentScenario.getTaskByName(self.scenarioTasks[self.menuTaskOptions.selectedIndex])
                self.taskDescription.setText(str(self.selectedTask.getDescription()))
                self.scenarioFrame.show()
        elif self.currentScenario == None:
            # add list of tasks to the GUI
            self.scenarioTasks =  self.currentScenario.getTaskList()
            self.menuTaskOptions['items'] = self.scenarioTasks
            # oddly, you cannot initialize with a font if there are no items in the menu
            # self.menuTaskOptions['item_text_font']=self.fonts['normal']
            # make sure some default task is selected
            self.selectedTask = self.currentScenario.getTaskByName(self.scenarioTasks[self.menuTaskOptions.selectedIndex])
            self.taskDescription.setText(str(self.selectedTask.getDescription()))

        self.scenarioFrame.show()
        self.toolbarFrame.show()
        self.scenarioBarControl.show()
        loadingText.destroy()

    def exitScenario(self):
        self.scenarioFrame.hide()
        self.scenarioBarControl.hide()

    def enterTaskPaused(self):
        #self.main.worldNode.show()
        self.start_simulation()
        self.taskFrame.show()
        self.taskBarControl.show()
       
    def exitTaskPaused(self):
        self.taskFrame.hide()
        self.taskBarControl.hide()

    def enterTaskTrain(self):
        self.taskFrame.show()
        self.taskBarControl.show()
        self.start_simulation()
        self.menuResetTrainingButton['text'] = "Training..."
        self.menuResetTrainingButton['state'] = DGG.DISABLED

    def exitTaskTrain(self):
        self.taskFrame.hide()
        self.taskBarControl.hide()
        self.menuResetTrainingButton['text'] = "Start training"
        self.menuResetTrainingButton['state'] = DGG.NORMAL

    def enterTaskTest(self):
        self.taskFrame.show()
        self.taskBarControl.show()
        self.start_simulation()
        self.selectedTask.start(True,self.onGoalMetCallback)
        self.menuTestButton['text']  = "Stop testing"
        self.menuTestButton['state'] = DGG.NORMAL

    def exitTaskTest(self):
        self.start_simulation()
        self.selectedTask.stop()
        self.menuTestButton['text'] = "Start testing"
        self.menuTestButton['state'] = DGG.NORMAL
        self.taskFrame.hide()

    def onGoalMetCallback(self):
        self.request('TaskPaused')
    
    
    def capture_agent_screenshot_pnm_image(self):
        pnm_image = PNMImage()
        success = self.agent_camera.getScreenshot(pnm_image)
        if not success:
            return None
        return pnm_image
        
    def capture_screenshot_pnm_image(self):
        pnm_image = PNMImage()
        success = self.base.camNode.getDisplayRegion(0).getScreenshot(pnm_image)
        if not success:
            return None
        return pnm_image
        
    #def capture_screenshot_xmlrpc_image(self):
    #    pnm_image = self.capture_screenshot_pnm_image()
    #    if pnm_image is None:
    #        return None
    #    return pnm_image__as__xmlrpc_image(pnm_image)

    def capture_screenshot_xmlrpc_image(self, max_x=None, max_y=None, x_offset=0, y_offset=0):
        return self.main.capture_xmlrpc_image(max_x=max_x, max_y=max_y, x_offset=x_offset, y_offset=y_offset)

    def capture_agent_screenshot_xmlrpc_image(self):
        pnm_image = self.capture_agent_screenshot_pnm_image()
        if pnm_image is None:
            return None
        return pnm_image__as__xmlrpc_image(pnm_image)

    def screenshot(self, name):
        pnm_image = self.capture_screenshot_pnm_image()
        if pnm_image is None:
            print 'Failed to save screenshot.  :('
            return None
        name = os.path.join("screenshots", name+"_")
        num = 0
        while os.path.exists(name+str(num)+".jpg"):
            num += 1
        filename = name+str(num)+".jpg"
        if pnm_image.write(Filename(filename)):
            print "Saved to ", filename
        else:
            print "Failed to saved to ", filename
        
    def screenshot_agent(self, name):
        pnm_image = self.capture_agent_screenshot_pnm_image()
        if pnm_image is None:
            print 'Failed to save screenshot.  :('
            return None
        name = os.path.join("screenshots", name+"_")
        num = 0
        while os.path.exists(name+str(num)+".jpg"):
            num += 1
        filename = name+str(num)+".jpg"
        if pnm_image.write(Filename(filename)):
            print "Saved to ", filename
        else:
            print "Failed to saved to ", filename
        
    def setAgentCamera(self, camera):
        self.agent_camera = camera

    def taskBarControlPress(self):
        if self.taskBarShown:
            self.taskFrame.hide()
            #self.taskBarControl.text = 'Show Taskbar'
        else:
            self.taskFrame.show()
            #self.taskBarControl.text = 'Hide Taskbar'
        self.taskBarShown = not self.taskBarShown

    def scenarioBarControlPress(self):
        if self.scenarioBarShown:
            self.scenarioFrame.hide()
            #self.scenarioBarControl.text = 'Show Scenario Options'
        else:
            self.scenarioFrame.show()
            #self.scenarioBarControl.text = 'Hide Scenario Options'
        self.scenarioBarShown = not self.scenarioBarShown

    def physics_is_active(self):
        return self.main.simulation_is_running()

    def download_isis_scenarios(self):

        self.http = HTTPClient()
        self.channel = self.http.makeChannel(True)
        self.channel.beginGetDocument(DocumentSpec('http://web.media.mit.edu/~dustin/isis_scenarios/'))
        self.rf = Ramfile()
        self.channel.downloadToRam(self.rf)

        def downloadTask( task):
            if self.channel.run():
                # Still waiting for file to finish downloading.
                return task.cont
            if not self.channel.isDownloadComplete():
                print "Error downloading file."
                return task.done
            data = self.rf.getData()
            print "got data:"
            print data
            return task.done
        
        taskMgr.add(downloadTask, 'download')
