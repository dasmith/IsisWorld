'''
The object that handles commands received via xmlrpc

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)
'''
from pandac.PandaModules import VBase3

class IsisCommandHandler(object):

    def __init__(self, simulator):
        self.simulator = simulator
        self.meta_commands  = ['meta_step','meta_pause','meta_list_actions','step_simulation']

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
            return 'failure'

        print "ID", agent_to_control
        if self.simulator.actionController.hasAction(cmd):
            # not a meta command and agent_to_control is defined
            # TODO: check to see if proper keys are defined for the given command
            return self._relayAgentControl(agent_to_control,cmd,args)
        elif cmd == 'meta_step':
            seconds = 0.05
            print "stepping simulator"
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.physicsManager.stepSimulation(seconds)
            return 'success'            
        elif cmd == 'step_simulation':
            print "WARNING, the step_simulation command will soon be deprecated. use 'meta_step' instead"
            seconds = 0.05
            print "stepping simulator"
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.physicsManager.stepSimulation(seconds)
            return 'success'
        elif cmd == 'meta_pause':
            self.simulator.physicsManager.togglePaused()
            return 'success'
        elif cmd == 'meta_list_actions':
            return self.simulator.actionController.actionMap.keys()+self.meta_commands
        else:
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



