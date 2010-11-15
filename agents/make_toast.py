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


print "Connected to IsisWorld"

scenarios = e.do('meta_list_scenarios')
print "Listing scenarios: %s" % (scenarios)

# load the toast scenario
print e.do('meta_load_scenario', {'scenario': 'make_toast.py'})

print 'Going into training mode'
print e.do('meta_train')

print "pausing"
print e.do('meta_pause')

do('look_down-start')
step(.4)
do('look_down-stop')

print "opening fridge"
do('pick_up_with_right_hand', {'target':'loaf'})

print "picking up"
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

# Try to use the knife to butter the toast
# Here I'm just following the format of the above code
print do('pick_up_with_right_hand', {'target':'knife'})
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