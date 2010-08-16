'''
The object that handles commands received via xmlrpc

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)
'''
from pandac.PandaModules import VBase3
import time
import os
from direct.stdpy.file import  *

class IsisCommandHandler(object):

    def __init__(self, simulator):
        self.simulator = simulator
        self.meta_commands  = ['meta_step','meta_pause','meta_resume','meta_list_actions','step_simulation']
        self.logger = Logger("logs")
        self.logger.createLog(str(int(time.time())), "Test scenario making toast", "Create toast")

    def handler(self,cmd,args={}):
        '''
        Takes command and optional labeled dictionary of arguments
        passed from the xmlrpc client and decides what to do with them.
        
        '''
        # debug statement
        print 'command %s received: (%s) ' % (cmd,','.join(['%s=%s' % (k,v) for k,v in args.items()]))
        # if command is a meta-command, it doesn't require an agent
        if cmd not in self.meta_commands and not self.simulator.actionController.hasAction(cmd):
            # don't know about this command
            print 'Unknown command: %s' % cmd
            print self.simulator.actionController.actionMap.values()
            self.logger.log("UNKNOWN COMMAND: "+cmd)
            return 'failure'
        agent_to_control = 0
        # trying to figure out the agent to control
        if args.has_key('agent') and args['agent'] in self.simulator.agentsNamesToIDs.keys():
            # if the name is defined and valid
            agent_to_control = self.simulator.agentsNamesToIDs[args['agent']]
        elif args.has_key('agent_id') and int(args['agent_id']) < len(self.simulator.agents):
            # if the agent id is defined and valid
            print "trying to control agent with ID", args['agent_id']
            agent_to_control = int(args['agent_id'])
            print agent_to_control

        elif cmd != "sense" and cmd not in self.meta_commands:
            # otherse, and if the commands require arguments (e.g., they are not meta-commands)
            print "Error: you must supply an agent either through 'agent'= name or 'agent_id' = id argument\n"
            print "Available agents:"
            for agent,id in self.simulator.agentsNamesToIDs.items():
                print "\t (%i)  %s\n" % (id,agent)
            self.logger.log(cmd + ": Error - No agent specified")
            return 'failure'

        print "ID", agent_to_control
        if self.simulator.actionController.hasAction(cmd):
            # not a meta command and agent_to_control is defined
            # TODO: check to see if proper keys are defined for the given command
            self.logger.log(cmd+", "+self.simulator.agents[agent_to_control].name+": Relayed to agent")
            return self._relayAgentControl(agent_to_control,cmd,args)
        elif cmd == 'meta_step':
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.physicsManager.stepSimulation(seconds)
            time.sleep(seconds)
            # dont accept new commands until this has stepped
            while self.simulator.physicsManager.stepping:   self.closed = True
            self.closed = False#time.sleep(0.00001)
            self.logger.log("step: "+str(seconds)+" seconds")
            return 'success'            
        elif cmd == 'step_simulation':
            print "WARNING, the step_simulation command will soon be deprecated. use 'meta_step' instead"
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.physicsManager.stepSimulation(seconds)
            # dont accept new commands until this has stepped
            while self.simulator.physicsManager.stepping:  self.closed = True
            self.closed = False
            return 'success'
        elif cmd == 'meta_pause':
            self.simulator.physicsManager.pause()
            self.logger.log("pause: Simulation paused")
            return 'success'
        elif cmd == 'meta_resume':
            self.simulator.physicsManager.resume()
            self.logger.log("resume: Simulation resumed")
            return 'success'
        elif cmd == 'meta_list_actions':
            return self.simulator.actionController.actionMap.keys()+self.meta_commands
        else:
            self.logger.log("UNKNOWN COMMAND: " + cmd)
            raise "Undefined meta command: %s" % cmd
        
        return "done"

    
    def _relayAgentControl(self, agentID, command, args):
        fullCmd = self.simulator.actionController.actionMap[command]
        return self.simulator.actionController.makeAgentDo(self.simulator.agents[agentID], fullCmd, args)

    #obsolete cruft
    def _handle_perception(self,args):
        raise NotImplementedError, "_handle_perception has moved to Ralph.control__sense"
    
    def handle_move_action(self,args):
        raise NotImplementedError, "handle_move_action through xmlrpc not implemented"

    def handle_pickup_action(pickup_array):
        raise NotImplementedError, "handle_pickup_action through xmlrpc not implemented"

    # teraforming methods
    def handle_object(self, args):
        """ Do appropriate thing with object type command """
        def handle_add_object(object_array):

            raise NotImplementedError, "handle_add_object through xmlrpc not implemented"

        def handle_remove_object(object_name):
            ''' Remove object from world using object_name '''
            raise NotImplementedError, "handle_remove_object through xmlrpc not implemented"


class Logger(object):
    def __init__(self, logDir = None):
        self.logFile = None
        self.logDir = logDir

    def createLog(self, title, scenario, task):
        self.closeLog()
        if self.logDir:
            title = os.path.join(self.logDir, title)

        if os.path.exists(title+".log"):
            logNum = 1
            while os.path.exists(title+"_"+str(logNum)+".log"):
                logNum += 1
            title += "__"+str(logNum)

        self.logFile = title+".log"
        self.log("date: "+time.asctime())
        self.log("scenario: "+scenario)
        self.log("task: "+task)
        self.log("")

    def openLog(self, title):
        self.logFile = title+".log"

    def closeLog(self):
        self.logFile = None

    def log(self, msg):
        if self.logFile:
            try:
                f = open(self.logFile, "a")
                f.write(msg+"\n")
                f.close()
            except IOError, e:
                print "Could not open log file %s for writing" % (self.logFile)
