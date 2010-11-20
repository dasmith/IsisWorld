import xmlrpclib as xml
import time

def connect_to_isis_world(server, port=8001):
    # connect to environment via XML-RPC
    e = xml.ServerProxy('http://%s:%i' % (server, port))
    print "Connecting to server"
    return e


e = connect_to_isis_world(server="localhost", port=8001)


def sense():
    return e.do('sense', {'agent':'Ralph'})

def step(t):
    e.do('meta_pause')
    e.do('meta_step', {'seconds':t})
    while e.do('meta_physics_active'):
        time.sleep(0.2)

def do(command, args = None):
    if not args:
        args = {}
    args['agent'] = 'Ralph'
    return e.do(command, args)

def get_obj_dict(item):
    objs = sense()['objects']
    true_key = None
    for key in objs.keys():
        if item in key: true_key = key
    if not true_key:
        return {}
    return objs[true_key]


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
