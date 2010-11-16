'''
The object that handles commands received via xmlrpc

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)
'''
from pandac.PandaModules import VBase3
import time
import os
import xmlrpclib
from direct.stdpy.file import  *
from multiprocessing import Queue

class IsisCommandHandler(object):
    
    waiting_command_queue  = Queue();
    finished_command_queue = Queue();
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.meta_commands  = ['meta_step','meta_pause','meta_resume','meta_reset','meta_list_actions','meta_list_scenarios', \
                                   'meta_load_scenario','meta_list_tasks','meta_load_task','meta_train','meta_test','meta_setup_thought_layers','step_simulation', \
                                   'meta_physics_is_active']
        #self.logger = Logger("logs")
        #self.logger.createLog(str(int(time.time())), "Test scenario making toast", "Create toast")
        
    def handler(self,cmd,args={}):
        '''
        Takes command and optional labeled dictionary of arguments
        passed from the xmlrpc client and decides what to do with them.
        '''
        # debug statement
        print 'command %s received: (%s) ' % (cmd,','.join(['%s=%s' % (k,v) for k,v in args.items()]))
        self.waiting_command_queue.put({'cmd':cmd, 'args':args})
        result = self.finished_command_queue.get()
        return result

    
    def next_waiting_command(self):
        try:
            return self.waiting_command_queue.get_nowait()
        except:
            return False

    def panda3d_thread_process_command_queue(self):
        next_command = self.next_waiting_command()
        while next_command:
            result = self.handle_next_command(next_command['cmd'], next_command['args'])
            self.finished_command_queue.put(result)
            next_command = self.next_waiting_command()
    
    def handle_next_command(self, cmd, args):
        """ This is called by the panda3d_thread_process_command_queue, issued by a separate
        thread defined in IsisTask. """
        if self.simulator.actionController.hasAction(cmd):
            # this command belongs to an agent, figure out which
            if args.has_key('agent') and args['agent'] in self.simulator.agentsNamesToIDs.keys():
                # if the name is defined and valid
                agent_to_control = self.simulator.agentsNamesToIDs[args['agent']]
            elif args.has_key('agent_id') and int(args['agent_id']) < len(self.simulator.agents):
                # if the agent id is defined and valid
                agent_to_control = int(args['agent_id'])
            else:
                # maybe the simulator has not loaded any agents
                if len(self.simulator.agents) == 0:
                    #self.logger.log("Error - Agent command issued when no agent is in simulator")
                    print "Error: there are no agents in the simulator!  Load a valid scene!"
                else:
                    #self.logger.log("Error - Agent command issued when no agent is in simulator")
                    print "Error: you must supply an agent either through 'agent'= name or 'agent_id' = id argument\n"
                    print "\nAvailable agents:"
                    for agent,id in self.simulator.agentsNamesToIDs.items():
                        print "\t (%i)  %s\n" % (id,agent)
                return 'failure'
            # Now we can relay the command to the agent 
            # TODO: check to see if proper keys are defined for the given command
            #self.logger.log(cmd+", "+self.simulator.agents[agent_to_control].name+": Relayed to agent")
            return self._relayAgentControl(agent_to_control,cmd,args)
        elif cmd == 'meta_step':
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.controller.step_simulation(seconds)
            # This function starts the simulator.  In order to tell when the simulation is finished, you need to use meta_
            #self.logger.log("step: "+str(seconds)+" seconds")
            return 'success'            
        elif cmd == 'meta_physics_active':
            if self.simulator.controller.physics_is_active():
                return 1
            return 0
        elif cmd == 'step_simulation':
            print "WARNING, the step_simulation command will soon be deprecated. use 'meta_step' instead"
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.controller.step_simulation(seconds)
            # dont accept new commands until this has stepped
            #while self.simulator.physicsManager.stepping:  self.closed = True
            self.closed = False
            return 'success'
        elif cmd == 'meta_pause':
            self.simulator.controller.pause_simulation()
            #self.logger.log("pause: Simulation paused")
            return 'success'
        elif cmd == 'meta_resume':
            self.simulator.controller.start_simulation()
            #self.logger.log("resume: Simulation resumed")
            return 'success'
        elif cmd == 'meta_screenshot':
            max_x = None
            if args.has_key('max_x'):
                max_x = args['max_x']
            max_y = None
            if args.has_key('max_y'):
                max_y = args['max_y']
            x_offset = 0
            if args.has_key('x_offset'):
                x_offset = args['x_offset']
            y_offset = 0
            if args.has_key('y_offset'):
                y_offset = args['y_offset']
            xmlrpc_image = self.simulator.controller.capture_screenshot_xmlrpc_image(max_x=max_x, max_y=max_y, x_offset=x_offset, y_offset=y_offset)
            if xmlrpc_image is None:
                return 'failure'
            return xmlrpc_image
        elif cmd == 'meta_list_actions':
            return self.simulator.actionController.actionMap.keys()+self.meta_commands
        elif cmd == 'meta_list_scenarios':
            return self.simulator.controller.scenarioFiles
        elif cmd == 'meta_list_tasks':
            if self.simulator.controller.currentScenario:
                return self.simulator.controller.currentScenario.getTaskList()
            else:
                return "error: no scenario loaded"            
        elif cmd == 'meta_load_scenario':
            """ Loads a particular scenario file """
            if args.has_key('scenario'):
                scenario_file = args['scenario']
                if scenario_file in self.simulator.controller.scenarioFiles:
                    self.simulator.controller.selectedScenario = scenario_file
                    return self.simulator.controller.safe_request('Scenario')
                else:
                    return "error: meta_load_scenario scenario value '%s' is invalid" % scenario_file
            else:
                return "error: meta_load_scenario requires 'scenario' argument"
        elif cmd == "meta_load_task":
            """ Loads a task of the current scenario """
            if not self.simulator.controller.currentScenario:
                return "error: cannot load task before loading a scenario"
            if not self.simulator.controller.state  in ['Scenario']:
                return "error: cannot change task from this state"
            if args.has_key('task'):
                task_name = args['task']
                if task_name in self.simulator.controller.currentScenario.getTaskList():
                    self.simulator.controller.selectedTask = self.simulator.controller.currentScenario.getTaskByName(task_name)
                    self.simulator.controller.taskDescription.setText(str(self.simulator.controller.selectedTask.getDescription()))
                    return self.simulator.controller.safe_request('TaskPaused')
                else:
                    # could not find task
                    return "error: meta_load_task task value '%s' is invalid" % task_name
            else:
                return "error: meta_load_task requires 'task' argument"
        elif cmd == "meta_train":
            """ Enters training mode """
            return self.simulator.controller.safe_request('TaskTrain')
        elif cmd == "meta_test":
            """ Enters testing mode """
            return self.simulator.controller.safe_request('TaskTest')
        elif cmd == 'meta_reset':
            return self.simulator.controller.reset_scenario()
        elif cmd == "meta_setup_thought_layers":
            """ initializes the GUI and components with which kinds of thoughts
            exist in the agent and which ones should be visualized. """
            if len(args.keys()) != 0:
                return self.simulator.controller.setup_thought_filters(args)
            else:
                return "error: you need to send a dictionary defining the thought layers"
        else:
            # command is in neither meta_commands or the agent_controller
            print 'Unknown command: %s' % cmd
            print self.simulator.actionController.actionMap.values()
            return 'failure'
            #self.logger.log("UNKNOWN COMMAND: " + cmd)
            raise "Undefined meta command: %s" % cmd
        
        return "done"
        
    
    
    def _relayAgentControl(self, agentID, command, args):
        fullCmd = self.simulator.actionController.actionMap[command]
        return self.simulator.actionController.makeAgentDo(self.simulator.agents[agentID], fullCmd, args)

    #obsolete cruft
    def _handle_perception(self,args):
        raise NotImplementedError, "_handle_perception has moved to Ralph.control__sense"


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
