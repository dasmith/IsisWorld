'''
The object that handles commands received via xmlrpc

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)
'''
from pandac.PandaModules import VBase3

class Command_Handler(object):

    def __init__(self, simulator):
        self.simulator = simulator

    def command_handler(self,cmd,args={}):
        '''
        Takes command and optional labeled dictionary of arguments
        passed from the xmlrpc client and decides what to do with them.
        
        '''
        print 'command %s received: (%s) ' % (cmd,','.join(['(%s=%s)' % (k,v) for k,v in args.items()]))

        agent_to_control = 0

        if args.has_key('agent') and args['agent'] in self.simulator.agentsNamesToIDs.keys():
            agent_to_control = self.simulator.agentsNamesToIDs[args['agent']]
        elif args.has_key('agent_id') and int(args['agent_id']) < len(self.simulator.agents[agent_to_control]):
            agent_to_control = int(args['agent_id'])
        else:
            print "Error: you must supply an agent either through 'agent'= name or 'agent_id' = id argument\n"
            print "Available agents:"
            for agent,id in self.simulator.agentsNamesToIDs.items():
                print "\t (%i)  %s\n" % (id,agent)
            return 'failure'
        if cmd == 'sense':
            return self.handle_perception(agent_to_control, args)
        elif cmd == 'turn_left-start':
            self.simulator.agents[agent_to_control].control__turn_left__start()
            return 'success'
        elif cmd == 'turn_left-stop':
            self.simulator.agents[agent_to_control].control__turn_left__stop()
            return 'success'
        elif cmd == 'turn_right-start':
            self.simulator.agents[agent_to_control].control__turn_right__start()
            return 'success'
        elif cmd == 'turn_right-stop':
            self.simulator.agents[agent_to_control].control__turn_right__stop()
            return 'success'
        elif cmd == 'move_forward-start':
            self.simulator.agents[agent_to_control].control__move_forward__start()
            return 'success'
        elif cmd == 'move_forward-stop':
            self.simulator.agents[agent_to_control].control__move_forward__stop()
            return 'success'
        elif cmd == 'move_backward-start':
            self.simulator.agents[agent_to_control].control__move_backward__start()
            return 'success'
        elif cmd == 'move_backward-stop':
            self.simulator.agents[agent_to_control].control__move_backward__stop()
            return 'success'
        elif cmd == 'look_left-start':
            self.simulator.agents[agent_to_control].control__look_left__start()
            return 'success'
        elif cmd == 'look_left-stop':
            self.simulator.agents[agent_to_control].control__look_left__stop()
            return 'success'
        elif cmd == 'look_right-start':
            self.simulator.agents[agent_to_control].control__look_right__start()
            return 'success'
        elif cmd == 'look_right-stop':
            self.simulator.agents[agent_to_control].control__look_right__stop()
            return 'success'
        elif cmd == 'look_up-start':
            self.simulator.agents[agent_to_control].control__look_up__start()
            return 'success'
        elif cmd == 'look_up-stop':
            self.simulator.agents[agent_to_control].control__look_up__stop()
            return 'success'
        elif cmd == 'look_down-start':
            self.simulator.agents[agent_to_control].control__look_down__start()
            return 'success'
        elif cmd == 'look_down-stop':
            self.simulator.agents[agent_to_control].control__look_down__stop()
            return 'success'
        elif cmd == 'pick_up_with_right_hand':
            if args.has_key('object'):
                pick_up_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for pick_up_with_right_hand command.'
            return self.simulator.agents[agent_to_control].control__pick_up_with_right_hand(pick_up_object)
        elif cmd == 'pick_up_with_left_hand':
            if args.has_key('object'):
                pick_up_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for pick_up_with_left_hand command.'
            return self.simulator.agents[agent_to_control].control__pick_up_with_left_hand(pick_up_object)
        elif cmd == 'drop_from_right_hand':
            return self.simulator.agents[agent_to_control].control__drop_from_right_hand()
        elif cmd == 'drop_from_left_hand':
            return self.simulator.agents[agent_to_control].control__drop_from_left_hand()
        elif cmd == 'use':
            if args.has_key('object'):
                use_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for use command.'
            if args.has_key('with_object'):
                with_object = args['with_object']
            else:
                return 'failure: need to define \'with_object\' slot for use command.'
            return self.simulator.agents[agent_to_control].control__use_object_with_object(use_object, with_object)
        elif cmd == 'say':
            if args.has_key('message'):
                utterance = args['message']
            else:
                return 'failure: need to define \'message\' slot for say command.'
            self.simulator.agents[agent_to_control].control__say(utterance)
            return 'success'
        elif cmd == 'step_simulation':
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.simulator.step_simulation(seconds)
            return 'success'
#        elif cmd in ['move','move to']:
#            return self.handle_move_action(args)
#        elif cmd == 'object':
#            return self.handle_object(args)
        else:
            print 'command %s not recognized' % (cmd)
            return False

        

    def handle_perception(self, agent_to_control, *args):
        """ perceives the world, returns percepts dict """
        percepts = dict()
        # eyes: visual matricies
        percepts['vision'] = self.simulator.get_agent_vision(agent_to_control)
        # objects in purview (cheating object recognition)
        percepts['objects'] = self.simulator.get_objects(agent_to_control)
        # global position in environment - our robots can have GPS :)
        percepts['position'] = self.simulator.get_agent_position(agent_to_control)
        # language: get last utterances that were typed
        percepts['language'] = self.simulator.get_utterances()
        return percepts

    
    def handle_move_action(self,args):
        raise NotImplementedError, "handle_move_action through xmlrpc not implemented"    
        #if args.has_key('target'):
        #    target_name = args['target']
        #    return self.simulator.move_agent_to_target(target_name)
        #elif args.has_key('x') and args.has_key('y') and args.has_key('z'):
        #    x = float(args['x'])
        #    y = float(args['y'])
        #    z = float(args['z'])
        #    position = VBase3(x, y, z)
        #    return self.simulator.move_agent_to_position(position)
        #else:
        #    return 'command not recognized'
    
    def handle_pickup_action(pickup_array):
        raise NotImplementedError, "handle_pickup_action through xmlrpc not implemented"    

     
    # teraforming methods 
    def handle_object(self, args):
        """ Do appropriate thing with object type command """
        def handle_add_object(object_array):
            
            raise NotImplementedError, "handle_add_object through xmlrpc not implemented"
            #''' Handles an object added to the world '''
            #id = 0 # default for now
            #name = object_array[0]
            #position = map(lambda(x): int(x), object_array[1:4])
            #if len(object_array) == 5:
            #    model = object_array[4]
            #else: model = 'models/sphere'
            #vo = Visual_Object(id, name, position, model=model)
            #world_name = self.simulator.put_object_in_world(vo)
            #return 'object added as: ' + world_name

        def handle_remove_object(object_name):
            ''' Remove object from world using object_name '''
            raise NotImplementedError, "handle_remove_object through xmlrpc not implemented"
       
        # TODO: update to dict-style arguments
        object_array = args.split(' ')
        if object_array[0] == 'add':
            return handle_add_object(object_array[1:])
        elif object_array[0] == 'remove':
            return handle_remove_object(object_array[1])
        return 'command not recognized'


        


