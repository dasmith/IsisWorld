import time


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
