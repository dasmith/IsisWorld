import time


from direct.gui.DirectGui import OkDialog
from pandac.PandaModules import ClockObject
from isis_goal import *

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
        
