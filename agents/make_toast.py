
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
do('look_down-start')
while get_obj_xy('loaf') < 0.5:
    step(.4)
do('look_down-stop')

print "picking up butter"
do('pick_up_with_left_hand', {'target':'butter'})
step(.2)

print "picking up loaf"
do('pick_up_with_right_hand', {'target':'loaf'})
step(0.8)

do('move_backward-start')
step(0.8)
do('move_backward-stop')

do('turn_left-start')
step(1.3)
do('turn_left-stop')

print "moving forward"
do('move_forward-start')
step(4)
do('move_forward-stop')

print "turning right"
do('turn_right-start')
step(1.3)
do('turn_right-stop')

print "moving forward"
do('move_forward-start')
step(3.6)
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
        full_table_name  = name.replace("IsisObject/","")

print do('use_right_hand', {'target':full_table_name, 'action':'put_on'})
step(.1)

print do('use_left_hand', {'target':full_table_name, 'action':'put_on'})
step(.1)

print "picking up knife"
print do('pick_up_with_right_hand', {'target':'knife'})
step(.1)
print do('use_right_hand', {'target':'loaf', 'action':'divide'})
step(.1)
print do('use_left_hand', {'target':'toaster', 'action':'put_in'})
step(.1)
print do('use_right_hand', {'target':'toaster', 'action':'turn_on'})
step(.1)

"""

print do('pick_up_with_right_hand', {'target':'knife'})
step(.1)
print do('use_right_hand', {'target':'loaf', 'action':'divide'})
step(.1)
print do('use_left_hand', {'target':'toaster', 'action':'put_in'})
step(.1)
print do('use_right_hand', {'target':'toaster', 'action':'turn_on'})
step(.1)

# Try to use the knife to butter the toast
# Here I'm just following the format of the above code

# I think the knife is already in the right hand, but uncomment the following 2 lines if I'm wrong
#print do('pick_up_with_right_hand', {'target':'knife'})
#step(.1)

# Pick up the butter with the left hand
print do('pick_up_with_left_hand', {'target':'butter'})
step(.1)

# Put the butter on the table
print do('use_left_hand', {'target':'table', 'action':'put_on'})
step(.1) 

# Spread the butter on the knife
print do('use_right_hand', {'target':'butter', 'action':'spread'})
step(.1)

# Pick up the toasted bread
print do('pick_up_with_left_hand', {'target':'toast'})
step(.1)


# Transfer the butter from the knife to the toasted bread
print do('use_right_hand', {'target':'toast', 'action':'transfer'})
step(.1)

"""