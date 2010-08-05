

class IsisScenario(object):
    
    def __init__(self,name):
        self.tasks = []
        self.name = name
        self._loadTaskFile(self.name)
    
    
    def _loadTaskFile(self,fileName):
        print "Loading: %s" % fileName
        execfile("scenarios/%s.py" % fileName,{},self.__dict__)
        print "locals", locals()
    
    
    def getTasks(self):
        return filter(lambda x: x[0:4] == "task",dir(self))
