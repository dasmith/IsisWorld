import time

from pandac.PandaModules import ClockObject
from direct.gui.DirectGui import OkDialog

from src.loader import *

class IsisParseProblem(Exception):    
    def __init__(self,message,component='unknown'):
        self.message = message
        self.component = component 

    def __str__(self):
        return repr(self.message)+repr(self.component)

class IsisGoal(object):
    """  Each Task has at least one goal, whose main
    body is a function that returns True or False depending
    on the state of the simulator.  This function is referenced
    in the funciton self._checkCode """
    
    def __init__(self, checkCode, scenario):
        self._checkCode = checkCode
        # store pointer to scenario to check for envVars
        self._scenario = scenario
        self._envDict = {}
        self._timeStarted = 0
        self._timeElapsed = 0
        self.complete = False
        
    def check(self):
        """ This is the checking function that is called at each 
        cycle that the Test round of the Task is running. Returns
        True when the goal has been met, and subsequently is not
        checked again until the goal is reset."""
        if self._timeStarted == 0:
            # initialize start time
            self._timeStarted = time.time()
        if eval(self._checkCode.__code__,self._scenario.envDict):
            self.complete = True
            # goal met!  save information about the goal
            self._timeElapsed = time.time()-self._timeStarted
            return True
        else:
            return False
    
    def completionString(self):
        if self.complete:
            return " MET! (%f sec)" % (self._timeElapsed)
        else:
            return " FAILED."
    
    def reset(self):
        """ Resets the state of the goal so that it can be run
        again. """
        self._timeStarted = 0
        self._timeElapsed = 0
        self.complete = False
        self._envDict.update(self._scenario.envDict)
        self._envDict['self']=self
    
class IsisTask(object):
    def __init__(self,scenario):
        self.description = None
        self._GlobalClock = ClockObject.getGlobalClock()
        self._scenario = scenario 
        self._goals = dict()

    def executeTaskCode(self,name,ref):
        """ Executes the task method"""
        #try:
        def save_locals(l):
            self.__dict__.update(l)
        self.__dict__.update({'task':self, 't':self,'store':save_locals})
        try:
            exec ref.__code__ in self.__dict__ # maps all mentions of 'task' to the self object.
        except Exception, e:
            raise IsisParseProblem(str(e),'task: %s' %  name)

        if not hasattr(self,'name'):
            self.name = name
       
        # parse out the goal functions
        _goal_functions =  filter(lambda x: x[0:4] == "goal",dir(self))

        if len(_goal_functions) == 0:
            raise IsisParseProblem("No goal defined in task.", "task: %s" % name)
        
        for gf in _goal_functions:    
            new_goal = IsisGoal(self.__dict__[gf], self._scenario)
            self._goals[gf] = new_goal 

    def start(self, captureMovie, controllerCallback):
        self.start_time = time.time()
        self.time = 0.0
        for gf in self._goals.values():
            gf.reset()
        # pointer of method to call in controller to signal
        # that the Testing phase has ended
        self.controllerCallback = controllerCallback 
        taskMgr.add(self._goalCheckTask,'goal-checking-task')
  
    def stop(self):
        taskMgr.remove('goal-checking-task')

    def onCompletion(self):
        """ Ends the testing method and displays the goal statistics in the window"""
        self.goal_statement = "Goals met!\n"
        for goal_name, goal_function in self._goals.items():
            self.goal_statement += "Goal %s: %s"  % (goal_name, goal_function.completionString())
        def closeDialog(arg):
            goal_dialog.cleanup() # hide window
        goal_dialog = OkDialog(text=self.goal_statement, command=closeDialog)
        # signal to controller that testing phase has ended
        self.controllerCallback()

    def onStatus(self):
        """ Prints out the current status of each goal, without any congratulatory message. """
        self.goal_statement = "Goal Status:\n"
        for goal_name, goal_function in self._goals.items():
            self.goal_statement += "Goal %s: %s"  % (goal_name, goal_function.completionString())
        def closeDialog(arg):
            goal_dialog.cleanup() # hide window
        goal_dialog = OkDialog(text=self.goal_statement, command=closeDialog)

    def _goalCheckTask(self,task): 
        all_done = True
        self.time = time.time()-self.start_time
        for goal_name, goal_function in self._goals.items():
            if not goal_function.complete and goal_function.check():
                print "GOAL %s FINISHED" % (goal_name)
            else:
                all_done = False
        if not all_done:
            return task.cont
        else:
            self.onCompletion()
            return task.done
    

    def getDescription(self):
        """ Builds the string that is presented in the Task GUI"""
        s = "TASK: %s\n" % self.name
        if self.description != None:
            s += self.description
        s += "\nAUTHOR: %s" % self._scenario.author 
        return s

    def _advanceTask(self, task):
        """ This method is added to Panda's task management and executed at each cycle
        whenever a task is running.  It checks to see if it's in training or testing mode. 
        This is responsible for saving screenshots at various intervals."""
        dt = self._GlobalClock.getDt()
        return task.cont
        
        

class IsisScenario(object):
    def __init__(self,name):
        # _taskDict stores a mapping of task names to task methods
        self._taskDict = {}
        self.name = name
        self.description = "No description"
        self.author = "Unknown"
        # envDict stores a mapping of variable names to isisObject and isisAgent instances
        self.envDict = {}
        self._loadTaskFile(self.name)
    
    def _loadTaskFile(self,fileName):
        print "Loading: %s" % fileName
        try:
            execfile("scenarios/%s.py" % fileName,{'scenario':self, 's':self},self.__dict__)
        except Exception, e:
            raise IsisParseProblem(str(e),fileName+".py")
        # load all of the tasks
        task_functions =  filter(lambda x: x[0:4] == "task",dir(self))
        if len(task_functions) == 0:
            raise IsisParseProblem("No tasks defined.",fileName)

        # create IsisTasks for each of the def task_* in the scenario file.
        for tf in task_functions:    
            new_task = IsisTask(self)
            new_task.executeTaskCode(tf,self.__dict__[tf])
            # add the task to the dictionary
            self._taskDict[new_task.name] = new_task

    def loadScenario(self, baseNode):
        try:
            load_objects(self, baseNode)
            return True
        except Exception, e:
            raise IsisParseProblem(str(e),"%s in def environment()" % self.name)
            return False

    def getTaskByName(self,taskName):
        return self._taskDict[taskName]
            
    def getTaskList(self):
        return self._taskDict.keys()
