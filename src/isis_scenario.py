
from src.loader import *
from isis_task import *

class IsisParseProblem(Exception):    
    def __init__(self,message,component='unknown'):
        self.message = message
        self.component = component 

    def __str__(self):
        return repr(self.message)+repr(self.component)


class IsisScenario(object):
    
    def __init__(self,filename):
        # _taskDict stores a mapping of task names to task methods
        self._taskDict = {}
        if hasattr(self,'name'):
            self.name = self.name
        else:
            self.name = filename
            
        self.description = "No description"
        self.author = "Unknown"
        # envDict stores a mapping of variable names to isisObject and isisAgent instances
        self.envDict = {}
        self._loadTaskFile(self.name)
    
    def _loadTaskFile(self,functionName):
        print "Loading: %s" % functionName
        
        # load all of the tasks
        task_functions =  filter(lambda x: x[0:4] == "task",dir(self))
        
        if len(task_functions) == 0:
            raise IsisParseProblem("No tasks defined.",functionName)

        # create IsisTasks for each of the def task_* in the scenario file.
        print "Self dictionary", self.__dict__.keys()
        for tf in task_functions:    
            new_task = IsisTask(self)
            new_task.executeTaskCode(tf,self.__getattribute__(tf))
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
    
    def __del__(self):
        """ Delete tasks """
        for task in self._taskDict.values():
            del task
        
