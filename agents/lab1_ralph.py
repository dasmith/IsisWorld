#!/usr/bin/env python

'''
A simple reactive agent that looks for the toas

Opens connection to local xmlrpc server on port 8001 and runs a reactive agent

Authors: Bo Morgan, Dustin Smith

History:
    0: 2010-03-17   Initial Release
    1: 2010-03-18   Added more comments
    2: 2010-03-22   Moved backchaining to DifferenceEngine class (som/arch.py)

'''

from som.arch import CriticSelectorArchitecture, DifferenceEngine, Critic, Selector

class ReactiveRalph(CriticSelectorArchitecture):
    """ Reactive Ralph has critic selector pairs for

       Upon initialization, it creates a connection with the XML-RPC server
    """

    def __init__(self,*args,**kwargs):
        CriticSelectorArchitecture.__init__(self,*args,**kwargs)

        # define components of difference engines
        # conditions: return True if some difference does not exist (goal met), or description of difference
        # actions: given description of differece (diff), try to remove the difference:
        #   - actions return True when they are active (require continuation at next cognitive cycle)
        #   - upon success or when stuck, they return False.

        def looking_straight_ahead(resource):
            print "DE3-condition (head not aligned with body)"
            if abs(resource.mind.perceptions['position']['neck_p']) < 2:
                return True
            else:
                return resource.mind.perceptions['position']['neck_p']

        def align_body_with_head(resource,diff):
            print "DE3-action (turn body to match head) diff=", diff
            if diff < -2:
                resource.mind.env.do('turn_right-start')
                return True
            elif diff > 2:
                resource.mind.env.do('turn_left-start')
                return True
            else:
                print "****** stopping turning ***"
                resource.mind.env.do('turn_right-stop')
                resource.mind.env.do('turn_left-stop')
                return False

        def has_in_center_of_view(resource,item='piece_of_toast'):
            print "DE2/DE4-(sub)condition (item in view)"
            if not resource.mind.perceptions['objects'].has_key(item):
                return False  # unquantifiable difference
            y_pos = resource.mind.perceptions['objects'][item]['y_pos']
            if abs(y_pos) > 0.25:
                return y_pos # difference
            else:
                return True # difference has been met

        def center_in_view(resource,diff,item='piece_of_toast'):
            print "DE4-action (center in view) diff=",diff
            if diff == False:
                return False
            else:
                if diff > 0.2:
                    resource.mind.env.do('look_right-start')
                    return True
                elif diff < -0.2:
                    resource.mind.env.do('look_left-start')
                    return True
                else:
                    # stop moving head
                    resource.mind.env.do('look_right-stop')
                    resource.mind.env.do('look_left-stop')
                    return False# we're done

        def has_in_view(resource, item='piece_of_toast'):
            print "DE1/DE5-condition (has item in view)"
            return resource.mind.perceptions['objects'].has_key(item)

        def is_within_reach(resource, item='piece_of_toast'):
            print "DE1/DE2-condition (can reach)"
            # if looking straight ahead at toast
            if has_in_view(resource, item='piece_of_toast') == True:
                if resource.mind.perceptions['objects'][item]['distance'] < 5.0:
                    return True
                else:
                    return resource.mind.perceptions['objects'][item]['distance']
            return False # unquantifiable difference

        def move_within_reach(resource, diff, item='piece_of_toast'):
            print "DE2-action (move within reach) diff=",diff
            if diff == False:
                return False
            if diff > 5.0:
                resource.mind.env.do('move_forward-start')
                return True # still working
            else:
                print "STOPPING MOVING"
                return False
                resource.mind.env.do('move_forward-stop')

        def pick_up_item_with_left_hand(resource,diff,item='piece_of_toast'):
            print "DE1-action (pick up item='piece_of_toast'), diff=",diff
            if diff == True:
                return resource.mind.env.do('pick_up_with_left_hand',{'object':item})
            else:
                return False # stuck, i don't know how to pick up when something's already there


        def turn_body(resource, diff):
            print "DE5-action (turn body)"
            if diff == False:
                # start looking an arbitrary direction
                resource.mind.env.do('turn_right-start')
                return True
            else:
                resource.mind.env.do('turn_right-stop')
                return False # done

        def some_reactive_resource_is_active(resource):
            print "DE6-condition (?)"
            return len(filter(lambda d: d.is_on and d.is_active, resource.mind.reactive_resources))!=0

        def do_this_when_bored(resource,diff):
            print "DE6-action (?)"
            if len(resource.mind.perceptions['objects'].keys()) != 0:
                resource.mind.env.do('turn_left-stop')
                return False
            else:
                resource.mind.env.do('turn_left-start')
                return True

        def nothing_in_left_hand(resource):
            print 'CRITIC CALLED'
            if resource.mind.perceptions['position']['in_left_hand'] == '':
                print "FIRED"
                return True
            else:
                return False


        # initialize difference engines
        locate_toast_by_turning_head                             = DifferenceEngine(self, has_in_view, turn_body)
        fixate_on_toast_by_moving_head                           = DifferenceEngine(self, has_in_center_of_view, center_in_view, [locate_toast_by_turning_head])
        turn_body_to_look_straight_ahead                         = DifferenceEngine(self, looking_straight_ahead, align_body_with_head)
        make_toast_within_reach_by_walking_forward               = DifferenceEngine(self, is_within_reach, move_within_reach,[fixate_on_toast_by_moving_head, turn_body_to_look_straight_ahead])
        pick_up_piece_of_toast                                   = DifferenceEngine(self,is_within_reach,pick_up_item_with_left_hand,[make_toast_within_reach_by_walking_forward])
        mysterious_selector_for_problem_set                      = DifferenceEngine(self,all_reactive_resources_are_inactive, do_this_when_bored)

        # initialize critiic
        pick_up_toast_critic = self.add_reactive_resource(Critic(self,nothing_in_left_hand,[pick_up_piece_of_toast]))
        pick_up_toast_critic.is_on = True # begin debugging
        def debug_selector(x):
            """ This prints out the positions of relevant perceptual components."""
            if x.mind.perceptions['objects'].has_key('piece_of_toast'):
                print "NECK: ", x.mind.perceptions['position']['neck_p'], "TOAST", x.mind.perceptions['objects']['piece_of_toast']['y_pos']
            return True

        #self.add_reflective_resource(Selector(self,debug_selector)).is_on = True

        # end __init__()

ralph = ReactiveRalph(debug=True) # set debug=False to hide many output messagesFKJ<LeftMouse>K<LeftMouse>
ralph.step()   # to step ralph once
# ralph.run(1) # to step ralph once
# ralph.run(2) # to run ralph 2x
# ralph.run()  # to run ralph indefinitely
