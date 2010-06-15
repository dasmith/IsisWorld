#!/usr/bin/env python

'''
agent that learns to predict reactive level action ("pick up(toast)")
'''

from som.arch import *
import som.frame_utils as frame_utils
import som.concept_learning as concept_learning

class DeliberativeRalph(CriticSelectorArchitecture):

    def __init__(self,*args,**kwargs):
        CriticSelectorArchitecture.__init__(self)

        # define mental resources, components of selectors (including DifferenceEngines, LearnedDifferenceEngines) and critics
        #
        # since Lab 2, DifferencesEngines are (two parts):
        #  (1) conditions: return True if some difference does not exist (goal met), or description of difference
        #  (2) actions: given description of differece (diff), try to remove the difference:
        #     - actions return True when they are active (require continuation at next cognitive cycle)
        #     - upon success or when stuck, they return False.

        def selector__react__looking_straight_ahead(resource):
            print "DE3-condition (head not aligned with body)"
            if abs(resource.mind.perceptions['position']['neck_p']) < 2:
                return True
            else:
                return resource.mind.perceptions['position']['neck_p']

        def selector__react__align_body_with_head(resource,diff):
            print "DE3-action (turn body to match head) diff=", diff
            if diff != True and diff < -2:
                resource.mind.env.do('turn_right-start')
                return True
            elif diff  != True and diff > 2:
                resource.mind.env.do('turn_left-start')
                return True
            else:
                print "****** stopping turning ***"
                resource.mind.env.do('turn_right-stop')
                resource.mind.env.do('turn_left-stop')
                return False

        def selector__react__has_in_center_of_view(resource,item='piece_of_toast'):
            print "DE2/DE4-(sub)condition (item in view)"
            if not resource.mind.perceptions['objects'].has_key(item):
                return False  # unquantifiable difference
            y_pos = resource.mind.perceptions['objects'][item]['y_pos']
            if abs(y_pos) > 0.35:
                return y_pos # difference
            else:
                return True # difference has been met

        def selector__react__center_in_view(resource,diff,item='piece_of_toast'):
            print "DE4-action (center in view) diff=",diff
            if diff == False:
                #print "DE4-action (center in view): done, diff == False."
                return False
            elif diff == True:
                #print "DE4-action (center in view): done, stopping turning head."
                # stop moving head
                resource.mind.env.do('look_right-stop')
                resource.mind.env.do('look_left-stop')
                resource.mind.env.do('turn_right-stop')
                resource.mind.env.do('turn_left-stop')
                self.diff_eng__turn_body_to_look_straight_ahead.is_on = False
                return False# we're done
            elif diff > 0.2:
                #print "DE4-action (center in view): done, diff > 0.2."
                resource.mind.env.do('look_right-start')
                return True
            elif diff < -0.2:
                #print "DE4-action (center in view): done, diff < -0.2."
                resource.mind.env.do('look_left-start')
                return True
            #else:
                #print "DE4-action (center in view): we'll be shut off soon."

        def selector__react__has_in_view(resource, item='piece_of_toast'):
            print "DE1/DE5-condition (has item in view)"
            return resource.mind.perceptions['objects'].has_key(item)

        def selector__react__is_within_reach(resource, item='piece_of_toast'):
            print "DE1/DE2-condition (can reach)"
            # if looking straight ahead at toast
            if selector__react__has_in_view(resource, item='piece_of_toast') == True:
                if resource.mind.perceptions['objects'][item]['distance'] < 5.0:
                    return True
                else:
                    return resource.mind.perceptions['objects'][item]['distance']
            return False # unquantifiable difference

        def selector__react__move_within_reach(resource, diff, item='piece_of_toast'):
            print "DE2-action (move within reach) diff=",diff
            if diff == False:
                resource.mind.env.do('move_forward-stop')
                return False
            if diff != True and diff > 5.0:
                resource.mind.env.do('move_forward-start')
                return True # still working
            else:
                print "STOPPING MOVING"
                resource.mind.env.do('move_forward-stop')
                return False

        def selector__react__pick_up_item_with_left_hand(resource,diff,item='piece_of_toast'):
            print "DE1-action (pick up item='piece_of_toast'), diff=",diff
            if diff == True:
                print "DE1-action (pick up item='piece_of_toast'): within range, so attempting to pick up."
                result = resource.mind.env.do('pick_up_with_left_hand',{'object':item})
                if result == 'success':
                    print "DE1-action (pick up item='piece_of_toast'): success, action complete."
                    self.diff_eng__turn_body_to_look_straight_ahead.is_on = False
                    self.diff_eng__fixate_on_toast_by_moving_head.is_on = False
                    resource.mind.env.do('look_right-stop')
                    resource.mind.env.do('look_left-stop')
                    resource.mind.env.do('turn_right-stop')
                    resource.mind.env.do('turn_left-stop')
                    return False # done
                else:
                    print "DE1-action (pick up item='piece_of_toast'): failure, try again next time."
                    return True # still working
            else:
                return False # stuck, i don't know how to pick up when something's already there

        def critic__react__something_in_left_hand(resource):
            print "DE7-condition (is something in left hand?)."
            if resource.mind.perceptions['position']['in_left_hand'] != '':
                return True
            else:
                return False

        def selector__react__drop_item_in_left_hand(resource,diff):
            print "DE7-action (drop item from left hand), diff=",diff
            if diff == True:
                print "DE7-action (drop item from left hand): item in hand, so dropping."
                result = resource.mind.env.do('drop_from_left_hand')
                if result == 'success':
                    print "DE7-action (drop item from left hand): success, action complete."
                    return False # done
                else:
                    print "DE7-action (drop item from left hand): failure, try again next time."
                    return True # still working
            else:
                return False # stuck, i don't know how to drop when not holding anything.

        def selector__react__turn_body(resource, diff):
            print "DE5-action (turn body), diff =%s" % (diff)
            if diff == False:
                # start looking an arbitrary direction
                resource.mind.env.do('turn_right-start')
                return True
            else:
                resource.mind.env.do('turn_right-stop')
                return False # done

        def selector__reflect__some_reactive_resource_is_active(resource):
            print "DE6-condition (?)"
            return len(filter(lambda d: d.is_on and d.is_active, resource.mind.reactive_resources))!=0

        def selector__reflect__do_this_when_bored(resource,diff):
            print "DE6-action (?)"
            if len(resource.mind.perceptions['objects'].keys()) != 0:
                resource.mind.env.do('turn_left-stop')
                return False
            else:
                resource.mind.env.do('turn_left-start')
                return True

        def critic__react__nothing_in_left_hand(resource):
            if resource.mind.perceptions['position']['in_left_hand'] == '':
                return True
            else:
                return False

        def critic__delib__locate_toast_is_on(resource):
            # only when it just switched on
            if self.diff_eng__locate_toast_by_turning_head in resource.mind.turned_on:
                print "C-Delib (locate toast turned on)"
                resource.is_on = False
                return True
            else:
                return False

        def critic__react__listen_for_teacher(resource):
            if resource.mind.perceptions['language'].__contains__('learn'):
                return True
            else:
                return False

        def critic__react__listen_for_drop_command(resource):
            if resource.mind.perceptions['language'].__contains__('drop'):
                return True
            else:
                return False

        def critic__react__listen_for_pick_up_toast_command(resource):
            if resource.mind.perceptions['language'].__contains__('pick up toast'):
                return True
            else:
                return False

        def diffeng__react__toast_in_left_hand(resource):
            if resource.mind.perceptions['position']['in_left_hand'] == 'piece_of_toast':
                return True
            else:
                return False

        def critic__react__can_pick_up_toast(resource):
            self.learning_to_pick_up_toast_diff_eng.concept_learner.print_hypotheses()
            if self.learning_to_pick_up_toast_diff_eng.concept_learner.in_concept(resource.mind.perceptions):
                return True
            else:
                return False

        def diffeng__react__pick_up_toast(resource):
            print "Trying to pick up toast"
            resource.mind.env.do('pick_up_with_left_hand',{'object':'piece_of_toast'})

        #### "scripted find-and-pick up toast" mental resources, (improved version of Lab 1) ####

        # Initialize difference engines
        self.diff_eng__turn_body_to_look_straight_ahead                    = DifferenceEngine(self, selector__react__looking_straight_ahead, selector__react__align_body_with_head)
        self.diff_eng__locate_toast_by_turning_head                        = DifferenceEngine(self, selector__react__has_in_view, selector__react__turn_body)
        self.diff_eng__fixate_on_toast_by_moving_head                      = DifferenceEngine(self, selector__react__has_in_center_of_view, selector__react__center_in_view,\
                                                                                    [self.diff_eng__turn_body_to_look_straight_ahead,\
                                                                                     self.diff_eng__locate_toast_by_turning_head])
        self.diff_eng__make_toast_within_reach_by_walking_forward          = DifferenceEngine(self, selector__react__is_within_reach, selector__react__move_within_reach,\
                                                                                    [self.diff_eng__fixate_on_toast_by_moving_head, \
                                                                                     self.diff_eng__turn_body_to_look_straight_ahead])
        self.diff_eng__pick_up_piece_of_toast                              = DifferenceEngine(self, selector__react__is_within_reach,selector__react__pick_up_item_with_left_hand,\
                                                                                    [self.diff_eng__make_toast_within_reach_by_walking_forward])
        self.diff_eng__mysterious_selector_for_problem_set                 = DifferenceEngine(self, selector__reflect__some_reactive_resource_is_active, selector__reflect__do_this_when_bored)

        # Initialize Critic and add to reactive resources
        self.critic__pick_up_toast                                         = self.add_reactive_resource(Critic(self,critic__react__nothing_in_left_hand,\
                                                                                    [self.diff_eng__pick_up_piece_of_toast]))
        self.critic__pick_up_toast.is_on = False  # set to true to turn on "pick up toast"



        ####  "learning picking up toast preconditions" mental resources (Lab 2) ####

        # This is the learning engine, which turns on _until_ it receives a positive example
        self.learning_to_pick_up_toast_diff_eng = self.add_reactive_resource(LearningDifferenceEngine(self, diffeng__react__toast_in_left_hand, diffeng__react__pick_up_toast))
        self.learning_to_pick_up_toast_diff_eng.is_on = False

        # This is a difference engine that drops the first item that appears in left hand.
        self.drop_item_in_left_hand_diff_eng = DifferenceEngine(self, critic__react__something_in_left_hand, selector__react__drop_item_in_left_hand)
        self.drop_item_in_left_hand_diff_eng.is_on = False

        # This Critic checks if the preconditions learned by the above difference engine are met,
        # and prints out the learned hypotheses even when the learner is not engaged  (doesn't turn on any selector)
        self.add_reactive_resource(Critic(self,critic__react__can_pick_up_toast)).is_on = True

        # This Critic-Selector pair waits for someone to type "learn" into the terminal and
        # then turns on the learn-to-pick-up-toast difference engine
        self.add_reactive_resource(Critic(self,critic__react__listen_for_teacher, [self.learning_to_pick_up_toast_diff_eng])).is_on = True
        # this should be turned on by deliberative learning critic

        # This Critic-Selector pair waits for someone to type "drop" into the terminal and
        # then turns on the drop-object-in-left-hand difference engine
        self.add_reactive_resource(Critic(self,critic__react__listen_for_drop_command, [self.drop_item_in_left_hand_diff_eng])).is_on = True

        # This Critic-Selector pair waits for someone to type "pick up toast" into the terminal and
        # then turns on the pick-up-piece-of-toast difference engine
        self.add_reactive_resource(Critic(self,critic__react__listen_for_pick_up_toast_command, [self.diff_eng__pick_up_piece_of_toast])).is_on = True




# initialize the cog arch
ralph = DeliberativeRalph(debug=False)

# run ralph for 20 seconds
# ralph.run(100,seconds=0.3)
# run ralph forever
ralph.run(0,seconds=0.3)
