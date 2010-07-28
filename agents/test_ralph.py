import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')
e.do('meta_pause')

def containsFridge(dict):
    for k in dict:
        if 'fridge' in k:
            return k
    return False

def sense():
    return e.do('sense', {'agent':'Ralph'})

def step(time):
    e.do('meta_step', {'seconds':time})

e.do('turn_right-start', {'agent':'Ralph'})
p = sense()
while not containsFridge(p['objects']):
    step(.2)
    p = sense()

fridge = containsFridge(p['objects'])
if p['objects'][fridge]['x_pos'] < 0:
    e.do('turn_left-start', {'agent':'Ralph'})
while abs(p['objects'][fridge]['x_pos']) > .5:
    step(.025)
    p = sense()
    print abs(p['objects'][fridge]['x_pos'])

e.do('turn_right-stop', {'agent':'Ralph'})
e.do('turn_left-stop', {'agent':'Ralph'})

e.do('move_forward-start', {'agent':'Ralph'})
while p['objects'][fridge]['distance'] > .5:
    print p['objects'][fridge]['y_pos']
    if p['objects'][fridge]['y_pos'] > .3:
        e.do('look_up-start', {'agent':'Ralph'})
    elif p['objects'][fridge]['y_pos'] < -.3:
        e.do('look_down-start', {'agent':'Ralph'})
    else:
        e.do('look_up-stop', {'agent':'Ralph'})
        e.do('look_down-stop', {'agent':'Ralph'})
    step(.01)
    p = sense()
        


# sense world
#perceptions = e.do('sense', {'agent':'Ralph'})
#print perceptions
# do something
#e.do('meta_pause')
#e.do('turn_right-start', {'agent':'Ralph'})
#e.do('meta_step',{'seconds':0.3})
#e.do('turn_right-stop', {'agent':'Ralph'})
#e.do('meta_step',{'seconds':0.1})
#e.do('move_forward-start', {'agent':'Ralph'})
#e.do('meta_step',{'seconds':0.1})
#e.do('move_forward-stop', {'agent':'Ralph'})
#e.do('use_right_hand', {'action': 'open', 'object': 'fridge', 'agent':'Ralph'})
#e.do('meta_step',{'seconds':0.3})