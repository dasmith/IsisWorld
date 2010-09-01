import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')

print "Connected to IsisWorld"

scenarios = e.do('meta_list_scenarios')
print "Listing scenarios: %s" % (scenarios)

# load the first scenario
print e.do('meta_load_scenario', {'scenario': scenarios[0]})


tasks = e.do('meta_list_tasks')
print "Listing tasks: %s" % (tasks)

# load the first task
print e.do('meta_load_task', {'task': tasks[0]})

print 'Going into training mode'
print e.do('meta_train')

e.do('meta_pause')

def sense():
    return e.do('sense', {'agent':'Ralph'})

def step(time):
    e.do('meta_step', {'seconds':time})

def do(command, args = None):
    if not args:
        args = {}
    args['agent'] = 'Ralph'
    return e.do(command, args)


p = None
fridge = None
do('turn_right-start', {'speed':180})
while fridge == None:
    step(.1)
    p = sense()
    for obj in p['objects'].keys():
        if obj.find("fridge") > -1:
            fridge = obj
            break

turn = 'turn_right'
if p['objects'][fridge]['x_pos'] < 0:
    turn = 'turn_left'
do(turn+'-start', {'speed':10})

while abs(p['objects'][fridge]['x_pos']) > .1:
    step(.075)
    p = sense()

do(turn+'-stop')
while p['objects'][fridge]['distance'] > 4:
    do('move_forward-start', {'speed':(p['objects'][fridge]['distance']-3)})
    if p['objects'][fridge]['y_pos'] > .75:
        turn = 'look_up'
        do(turn+'-start', {'speed':15})
    elif p['objects'][fridge]['y_pos'] < .45:
        turn = 'look_down'
        do(turn+'-start', {'speed':15})
    else:
        do(turn+'-stop')
    step(.02)
    p = sense()
do(turn+'-stop')
do('move_forward-stop')

do('use_right_hand', {'target':fridge, 'action':'open'})
step(.5)
do('pick_up_with_right_hand', {'target':'loaf'})

do('move_right-start')
step(.4)
do('move_right-stop')

do('move_forward-start')
step(.5)
do('move_forward-stop')

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
