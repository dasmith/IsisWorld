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
    e.do(command, args)

def test_turn(time, speed = 360):
    h = sense()['position']['body_h']
    do('turn_left-start', {'speed':speed})
    step(time)
    do('turn_left-stop')
    return sense()['position']['body_h']-h

def test_move(time, speed = 10):
    p = sense()
    x = p['position']['body_x']
    y = p['position']['body_y']
    do('move_forward-start', {'speed':speed})
    step(time)
    do('move_forward-stop')
    p = sense()
    return ((p['position']['body_x']-x)**2+(p['position']['body_y']-y)**2)**.5

print test_turn(36, 10)
print test_move(1, 1)
