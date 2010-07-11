import xmlrpclib as xml
# connect to environment via XML-RPC
e = xml.ServerProxy('http://localhost:8001')
# sense world
perceptions = e.do('sense', {'agent':'Ralph'})
# do something
e.do('say',{'message':"Hello world!",'agent':'Ralph'})
e.do('say',{'message':"Hello Lauren!",'agent':'Lauren'})
# simulator is paused by default
# run for X=0.02 seconds


e.do('meta_pause',{'seconds':0.1, 'agent': 'Ralph'})
e.do('meta_step',{'seconds':0.1, 'agent': 'Ralph'})
e.do('meta_resume',{'seconds':0.1, 'agent': 'Ralph'})

e.do('say',{'message':"Hello worldsdfa!",'agent':'Lauren'})
e.do('meta_pause',{'seconds':0.02, 'agent': 'Ralph'})
