
from arch import *
import utils

# DifferencesEngines are (two parts):
#  (1) conditions: return True if some difference does not exist (goal met), or description of difference
#  (2) actions: given description of differece (diff), try to remove the difference:
#     - actions return True when they are active (require continuation at next cognitive cycle)
#     - upon success or when stuck, they return False.


##### CONDITION FUNCTIONS ##### 

def get_sensor(cnxns):
    try:
        sensor = cnxns["sensor"]
        perceptions = sensor.perceptions
        return sensor
    except(KeyError):
        print "Perceptual condition requires a 'sensor' connection with a 'perceptions' attribute."
        raise

def condition__react__something_in_left_hand(connections=[]):
    """
    condition__react__something_in_left_hand is a perception-based condition function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    if not 'position' in perceptions:
        print "I don't perceive any positions."
    if perceptions['position']['in_left_hand'] != '':
        return True
    else:
        return False
      
def condition__react__nothing_in_left_hand(connections=[]):
    """
    condition__react__nothing_in_left_hand is a perception-based condition function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    if not 'position' in perceptions:
        print perceptions
        print "I don't perceive any positions."
        return True
    elif perceptions['position']['in_left_hand'] == '':
        return True
    else:
        return False

def condition__react__has_in_view(item='piece_of_toast', connections=[]):
    """
    condition__react__has_in_view is a perception-based condition function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    return perceptions['objects'].has_key(item)


##### DIFFERENCE FUNCTIONS #####

# These are much like condition functions, but return values other than True if
# there is a quantifiable difference away from being satisfied


def difference__react__looking_straight_ahead(connections=[]):
    """
    difference__react__looking_straight_ahead is a perception-based difference function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    if abs(perceptions['position']['neck_p']) < 2: # TODO: get rid of magic numbers?
                                                   # TODO: link associated diff and action functions!
        return True
    else:
        return perceptions['position']['neck_p']

def difference__react__has_in_center_of_view(item='piece_of_toast', connections=[]):
    """
    difference__react__has_in_center_of_view is a perception-based difference function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    if not perceptions['objects'].has_key(item):
        return False  # unquantifiable difference
    y_pos = perceptions['objects'][item]['y_pos']
    if abs(y_pos) > 0.35:
        return y_pos # difference
    else:
        return True # difference has been met

def difference__react__is_within_reach(item='piece_of_toast', connections=[]):
    """
    difference__react__is_within_reach is a perception-based difference function.
    It expects an "sensor" connection with a "perceptions" attribute.
    """
    perceptions = get_sensor(connections).perceptions
    # if looking straight ahead at toast
    if condition__react__has_in_view(item, connections) == True:
        # NOTICE: this function is able to call another function modularly, making a temporary one that
        # uses whatever connections the outer function has, not some predefined hardwired connections for
        # the inner one. It's like the outer function is making its own copy, but without copying anything!
        if perceptions['objects'][item]['distance'] < 5.0:
            return True
        else:
            return perceptions['objects'][item]['distance']
    else:
        return False # unquantifiable difference


##### ACTION FUNCTIONS #####

def get_env(connections):
    try:
        return connections["env"]
    except(KeyError):
        print "Action requires an 'env' connection"
        raise

def action__react__pick_up_toast(diff=None, connections=[]):
    """
    action__react__pick_up_toast is a diff action.
    It expects an "env" connection where it can perform env.do actions.
    """
    print "Trying to pick up toast"
    env = get_env(connections)
    env.do('pick_up_with_left_hand',{'object':'piece_of_toast'})

def action__react__align_body_with_head(diff, connections=[]):
    """
    action__react__align_body_with_head is a diff action.
    It expects an "env" connection where it can perform env.do actions.
    """
    env = get_env(connections)

    if diff != True and diff < -2:
        env.do('turn_right-start')
        return True
    elif diff  != True and diff > 2:
        env.do('turn_left-start')
        return True
    else:
        print "****** stopping turning ***"
        env.do('turn_right-stop')
        env.do('turn_left-stop')
        return False

def action__react__move_within_reach(diff, item='piece_of_toast', connections=[]):
    """
    action__react__move_within_reach is a diff action.
    It expects an "env" connection where it can perform env.do actions.
    """
    env = get_env(connections)
    if diff == False:
        env.do('move_forward-stop')
        return False
    if diff != True and diff > 5.0:
        env.do('move_forward-start')
        return True # still working
    else:
        print "STOPPING MOVING"
        env.do('move_forward-stop')
        return False

def action__react__turn_body(diff, connections=[]):
    """
    action__react__turn_body is a diff action.
    It expects an "env" connection where it can perform env.do actions.
    """
    env = get_env(connections)

    print "DE5-action (turn body), diff =%s" % (diff)
    if diff == False:
        # start looking an arbitrary direction
        env.do('turn_right-start')
        return True
    else:
        env.do('turn_right-stop')
        return False # done


##### ABSTRACT RESOURCES #####  

abstract_diff_eng__turn_body_to_look_straight_ahead = AbstractDifferenceEngine(
    difference__react__looking_straight_ahead,
    action__react__align_body_with_head,
    [])
