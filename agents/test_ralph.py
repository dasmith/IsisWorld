import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')
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
    step(.1)
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

do('use_right_hand', {'target':'fridge', 'action':'open'})
step(.5)
print do('pick_up_with_right_hand', {'target':'loaf'})
