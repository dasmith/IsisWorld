import xmlrpclib as xml
import time
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
    
    
layer_config = {'0': {'name': 'Reactive'}, '1':{'name':'Deliberative','color':[0.9,0.8,0.3,1]}, '2': {'name':'Reflective'}}

print "Connected to IsisWorld"
scenarios = e.do('meta_list_scenarios')
print e.do('meta_load_scenario', {'scenario': scenarios[0]})
tasks = e.do('meta_list_tasks')
print e.do('meta_load_task', {'task': tasks[0]})
print e.do("meta_setup_thought_layers", layer_config)
print 'Going into training mode'
print e.do('meta_train')



while True:
    for key, layer in layer_config.items():
        msg = "Thought in the %s layer." % layer['name']
        do("think",{'message':msg, 'layer': key})
        time.sleep(1)
