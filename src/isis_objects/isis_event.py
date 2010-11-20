

class IsisEvent(object):
    
    def __init__(self, precondition_check, increment, termination_check, on_complete):
        
        self.__precondition_check = precondition_check
        self.__termination__check = termination_check
        
        # check to see if preconditions are met
        if self.__precondition_check():
            taskMgr.add()
        else:
    
    def update(self, task):
        """ This function is called each time """
        self.__increment()
        
    
    
    
    def dump_event_state(self):
        """ Produces a desription of the state of the function"""
        return []