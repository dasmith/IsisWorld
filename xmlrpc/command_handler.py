'''
The object that handles commands received via xmlrpc

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)
'''
from visual.visual_object import Visual_Object

from pandac.PandaModules import VBase3

class Command_Handler(object):

    def __init__(self, agent_simulator):
        self.agent_simulator = agent_simulator

    def command_handler(self, cmd,args={}):
        '''
        Takes command and optional labeled dictionary of arguments
        passed from the xmlrpc client and decides what to do with them.
        
        '''
        print 'command %s received: (%s) ' % (cmd,','.join(['(%s=%s)' % (k,v) for k,v in args.items()]))

        if cmd == 'sense':
            return self.handle_perception(args)
        elif cmd == 'turn_left-start':
            self.agent_simulator.agent.control__turn_left__start()
            return 'success'
        elif cmd == 'turn_left-stop':
            self.agent_simulator.agent.control__turn_left__stop()
            return 'success'
        elif cmd == 'turn_right-start':
            self.agent_simulator.agent.control__turn_right__start()
            return 'success'
        elif cmd == 'turn_right-stop':
            self.agent_simulator.agent.control__turn_right__stop()
            return 'success'
        elif cmd == 'move_forward-start':
            self.agent_simulator.agent.control__move_forward__start()
            return 'success'
        elif cmd == 'move_forward-stop':
            self.agent_simulator.agent.control__move_forward__stop()
            return 'success'
        elif cmd == 'move_backward-start':
            self.agent_simulator.agent.control__move_backward__start()
            return 'success'
        elif cmd == 'move_backward-stop':
            self.agent_simulator.agent.control__move_backward__stop()
            return 'success'
        elif cmd == 'look_left-start':
            self.agent_simulator.agent.control__look_left__start()
            return 'success'
        elif cmd == 'look_left-stop':
            self.agent_simulator.agent.control__look_left__stop()
            return 'success'
        elif cmd == 'look_right-start':
            self.agent_simulator.agent.control__look_right__start()
            return 'success'
        elif cmd == 'look_right-stop':
            self.agent_simulator.agent.control__look_right__stop()
            return 'success'
        elif cmd == 'look_up-start':
            self.agent_simulator.agent.control__look_up__start()
            return 'success'
        elif cmd == 'look_up-stop':
            self.agent_simulator.agent.control__look_up__stop()
            return 'success'
        elif cmd == 'look_down-start':
            self.agent_simulator.agent.control__look_down__start()
            return 'success'
        elif cmd == 'look_down-stop':
            self.agent_simulator.agent.control__look_down__stop()
            return 'success'
        elif cmd == 'pick_up_with_right_hand':
            if args.has_key('object'):
                pick_up_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for pick_up_with_right_hand command.'
            return self.agent_simulator.agent.control__pick_up_with_right_hand(pick_up_object)
        elif cmd == 'pick_up_with_left_hand':
            if args.has_key('object'):
                pick_up_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for pick_up_with_left_hand command.'
            return self.agent_simulator.agent.control__pick_up_with_left_hand(pick_up_object)
        elif cmd == 'drop_from_right_hand':
            return self.agent_simulator.agent.control__drop_from_right_hand()
        elif cmd == 'drop_from_left_hand':
            return self.agent_simulator.agent.control__drop_from_left_hand()
        elif cmd == 'use':
            if args.has_key('object'):
                use_object = args['object']
            else:
                return 'failure: need to define \'object\' slot for use command.'
            if args.has_key('with_object'):
                with_object = args['with_object']
            else:
                return 'failure: need to define \'with_object\' slot for use command.'
            return self.agent_simulator.agent.control__use_object_with_object(use_object, with_object)
        elif cmd == 'say':
            if args.has_key('message'):
                utterance = args['message']
            else:
                return 'failure: need to define \'message\' slot for say command.'
            self.agent_simulator.agent.control__say(utterance)
            return 'success'
        elif cmd == 'step_simulation':
            seconds = 0.05
            if args.has_key('seconds'):
                seconds = args['seconds']
            self.agent_simulator.step_simulation_time(seconds)
            return 'success'
#        elif cmd in ['move','move to']:
#            return self.handle_move_action(args)
#        elif cmd == 'object':
#            return self.handle_object(args)
        else:
            print 'command %s not recognized' % (cmd)
            return False

        

    def handle_perception(self, *args):
        """ perceives the world, returns percepts dict """
        percepts = dict()
        # eyes: visual matricies
        percepts['vision'] = self.agent_simulator.get_agent_vision()
        # objects in purview (cheating object recognition)
        percepts['objects'] = self.agent_simulator.get_objects()
        # global position in environment - our robots can have GPS :)
        percepts['position'] = self.agent_simulator.get_agent_position()
        # language: get last utterances that were typed 
        print "Sensing language"
        percepts['language'] = self.agent_simulator.get_utterances()
        print "Sensing language 2"
        return percepts

    
    def handle_move_action(self,args):
        if args.has_key('target'):
            target_name = args['target']
            return self.agent_simulator.move_agent_to_target(target_name)
        elif args.has_key('x') and args.has_key('y') and args.has_key('z'):
            x = float(args['x'])
            y = float(args['y'])
            z = float(args['z'])
            position = VBase3(x, y, z)
            return self.agent_simulator.move_agent_to_position(position)
        else:
            return 'command not recognized'
    
    def handle_pickup_action(pickup_array):
        pass    

     
    # teraforming methods 
    def handle_object(self, args):
        """ Do appropriate thing with object type command """
        def handle_add_object(object_array):
            ''' Handles an object added to the world '''
            id = 0 # default for now
            name = object_array[0]
            position = map(lambda(x): int(x), object_array[1:4])
            if len(object_array) == 5:
                model = object_array[4]
            else: model = 'models/sphere'
            vo = Visual_Object(id, name, position, model=model)
            world_name = self.agent_simulator.put_object_in_world(vo)
            return 'object added as: ' + world_name

        def handle_remove_object(object_name):
            ''' Remove object from world using object_name '''
            return self.agent_simulator.remove_object_from_world(object_name)
       
        # TODO: update to dict-style arguments
        object_array = args.split(' ')
        if object_array[0] == 'add':
            return handle_add_object(object_array[1:])
        elif object_array[0] == 'remove':
            return handle_remove_object(object_array[1])
        return 'command not recognized'


        


