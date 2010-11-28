#! /usr/bin/env python
from pandac.PandaModules import loadPrcFileData
import os
import imp
from panda3d.core import ExecutionEnvironment, Filename
from pandac.PandaModules import * # TODO: specialize this import
from direct.showbase.ShowBase import ShowBase 
from direct.stdpy import threading, file
print "Threads supported?", Thread.isThreadingSupported()


class IsisWorld(ShowBase):
    
    def __init__(self):
        ShowBase.__init__(self)
        self.scenarioFiles = []

        # check users local files and copy them over.
        print "Local", os.listdir("scenarios")
        rootDir = "subdir" 
        for scenarioPath in os.listdir(rootDir):
            scenarioFile = scenarioPath[scenarioPath.rfind("/")+1:]
            if "__init__" not in scenarioFile:
                print "Appending scenario file", scenarioFile
                self.scenarioFiles.append(scenarioFile)
      
        # user selects one of these files
        self.selectedScenario = self.scenarioFiles[0]

        # try to open the s.o.b.
        if self.selectedScenario.lower()[-3:] == '.py':
            print "Loading scenario file [py]", scenarioFile
            py_mod = imp.load_source(self.selectedScenario[:-3], rootDir+"/"+self.selectedScenario)
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
            self.currentScenario = py_mod.Go()
            print self.currentScenario

iw = IsisWorld()
iw.run()
