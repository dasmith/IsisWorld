
from isis_agent_tools import *

scenarios = e.do('meta_list_scenarios')
print "Listing scenarios: %s" % (scenarios)


# load the toast scenario
print e.do('meta_load_scenario', {'scenario': 'make_toast.py'})

tasks = e.do('meta_list_tasks')
print "Listing tasks: %s" % (tasks)

# load the toast scenario
print e.do('meta_load_task', {'task': tasks[0]})

print 'Going into training mode'
print e.do('meta_train')

print "Waiting for agent to drop"
import time
time.sleep(5)

print "pausing"
print e.do('meta_pause')

# look for the toast
print "Looking down to the loaf"
print do('look_down-start')
while get_obj_xy('egg') < 0.5:
    step(.4)
do('look_down-stop')

print "picking up egg"
do('pick_up_with_right_hand', {'target':'egg'})
step(0.8)

do('move_backward-start')
step(0.35)
do('move_backward-stop')

do('turn_left-start')
step(0.28)
do('turn_left-stop')

print "moving forward"
do('move_forward-start')
step(1)
do('move_forward-stop')

print "turning right"
do('turn_right-start')
step(0.25)
do('turn_right-stop')

print "moving forward"
do('move_forward-start')
step(.3)
do('move_forward-stop')

"""
"table" is not descriptive enough because there are 3.
We need to get the FULL name of the table in the agent's perceptions
"""

do('look_down-start')
while not get_obj_xy('table'):
    step(.4)
do('look_down-stop')


objs = sense()['objects']
full_table_name = None
for name in objs.keys():
    if "table" in name: 
        full_table_name  = name

print do('use_right_hand', {'target':full_table_name, 'action':'put_on'})
step(.1)

print do('use_left_hand', {'target':full_table_name, 'action':'put_on'})
step(.1)

print "picking up frying_pan"
print do('pick_up_with_left_hand', {'target':'frying_pan'})
step(.2)

print "picking up knife"
print do('pick_up_with_right_hand', {'target':'knife'})
step(.1)
print do('use_right_hand', {'target':'loaf', 'action':'divide'})
step(.1)
print do('use_left_hand', {'target':'toaster', 'action':'put_in'})
step(.1)
print do('use_right_hand', {'target':'toaster', 'action':'turn_on'})
step(.1)

do('look_left-start')
while not get_obj_xy('toaster'):
    step(.1)
do('look_left-stop')

while get_obj_dict('toaster')['attributes']['is_on']:
    print "waiting for toaster"
    step(.1)

print "picking up toast"
do('pick_up_with_left_hand', {'target':'bread'})
step(0.8)
print "scooping butter"
print do('use_right_hand', {'target':'butter', 'action':'scoop'})
step(.1)
print "wiping butter on bread"
print do('use_right_hand', {'target':'bread', 'action':'wipe'})
step(.1)
