import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')
# sense world
perceptions = e.do('sense', {'agent':'Ralph'})
print perceptions
# do something
e.do('meta_pause')
e.do('turn_right-start', {'agent':'Ralph'})
e.do('meta_step',{'seconds':0.3})
e.do('turn_right-stop', {'agent':'Ralph'})
e.do('meta_step',{'seconds':0.1})
e.do('move_forward-start', {'agent':'Ralph'})
e.do('meta_step',{'seconds':0.1})
e.do('move_forward-stop', {'agent':'Ralph'})
e.do('use_right_hand', {'action': 'open', 'object': 'fridge', 'agent':'Ralph'})
e.do('meta_step',{'seconds':0.3})