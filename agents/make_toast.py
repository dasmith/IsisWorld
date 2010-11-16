import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')

def sense():
    return e.do('sense', {'agent':'Ralph'})

def step(time):
    e.do('meta_step', {'seconds':time})

def do(command, args = None):
    if not args:
        args = {}
    args['agent'] = 'Ralph'
    return e.do(command, args)

def get_obj_xy(item):
    objs = sense()['objects']
    true_key = None
    for key in objs.keys():
        if item in key: true_key = key
    if not true_key:
        return False
    return (objs[true_key]['x_pos'], objs[true_key]['y_pos'])

def move_in_front_of_item(item):
    objs = sense()['objects']
    e.do('move_right-start')
    while not item in objs.keys():
        break
        


print "Connected to IsisWorld"

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
time.sleep(2)

print "pausing"
print e.do('meta_pause')


do('look_down-start')
while get_obj_xy('loaf') < 0.5:
    step(.4)

do('look_down-stop')

print "picking up butter"
do('pick_up_with_left_hand', {'target':'butter'})

print "picking up loaf"
do('pick_up_with_right_hand', {'target':'loaf'})

do('move_backward-start')
time.sleep(0.8)
do('move_backward-stop')

do('turn_left-start')
time.sleep(2)
do('turn_left-stop')

print do('use_right_hand', {'target':'table', 'action':'put_on'})
step(.1)
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