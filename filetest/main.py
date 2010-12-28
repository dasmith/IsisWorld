#! /usr/bin/env python
from pandac.PandaModules import loadPrcFileData
import os
import imp
from panda3d.core import ExecutionEnvironment, Filename
from pandac.PandaModules import * # TODO: specialize this import
from direct.showbase.ShowBase import ShowBase 
from direct.stdpy import threading, file
print "Threads supported?", Thread.isThreadingSupported()


def find_scenarios_directory():
    print "Finding Scenarios Directory."
    if base.appRunner:
        prefix = "../"
    else:
        prefix = ""
    # check environment variable
    try:
        print "1. ISIS_SCENARIO_PATH Environment variable...",
        environ = os.environ["ISIS_SCENARIO_PATH"]
        print "[%s] " % environ, 
        if Filename(environ).exist():
            print "OK"
            return environ
        else:
            print "NOT FOUND"
    except KeyError, e:
        print " NONE"
    locald = Filename(os.path.join(os.getcwd(),'scenarios')).toOsSpecific()
    print "2. Looking in local directory...[%s] " % locald,
    if Filename(locald).exists():
        print "OK"
        return locald
    else:
        print "NOT FOUND"
    localpd = Filename(os.path.join(prefix+os.getcwd(),'scenarios')).toOsSpecific()
    print "3. Looking in prefix + local directory...[%s] " % localpd,
    if Filename(localpd).exists():
        print "OK"
        return localpd
    else:
        print "NOT FOUND"
    
class IsisWorld(ShowBase):
    
    def __init__(self):
        ShowBase.__init__(self)
        self.scenarioFiles = []
        scenarios_dir =  find_scenarios_directory()
        for scenarioPath in sorted(os.listdir(scenarios_dir)):
            print scenarioPath, scenarioPath[-3:] 
            if scenarioPath[-3:] == ".py":         
                scenarioFile = scenarioPath[scenarioPath.rfind("/")+1:]
                self.scenarioFiles.append(scenarioFile)
                print "- Adding Scenario File: ", scenarioFile
      
        # user selects one of these files
        self.selectedScenario = self.scenarioFiles[0]
        #if self.selectedScenario.lower()[-3:] == '.py':
        #    print "Loading scenario file [py]", scenarioFile
        py_mod = imp.load_source(self.selectedScenario[:-3], scenarios_dir+"/"+self.selectedScenario)
        #elif self.selectedScenario.lower()[-4:] == '.pyo':
        
iw = IsisWorld()
iw.run()
