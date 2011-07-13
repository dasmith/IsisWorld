
from isis_agent_tools import *

scenarios = e.do('meta_list_scenarios')
print "Listing scenarios: %s" % (scenarios)


# load the toast scenario
#print e.do('meta_load_scenario', {'scenario': 'make_toast.py'})

tasks = e.do('meta_list_tasks')
print "Listing tasks: %s" % (tasks)

# load the toast scenario
#print e.do('meta_load_task', {'task': tasks[0]})

print 'Going into training mode'
print e.do('meta_train')

print "Waiting for agent to drop"
import time
time.sleep(5)

print "pausing"
print e.do('meta_pause')

blocks = []
objs = sense()['objects']
full_table_name = None
for name in objs.keys():
    if "block" in name: 
        blocks.append(name)
        
print "Looking down to the block"
print do('look_down-start')
while get_obj_xy('block') < 0.5:
    step(.4)
    
do('look_down-stop')

do('pick_up_with_left_hand', {"target": blocks[0]})
step(.2)
print do('use_left_hand', {'target':blocks[1], 'action':'put_on'})
step(.1)



