environment = """kitchen	at 0,0,0
toaster	at 0,0,8
table	in kitchen
toaster	on table
loaf	on table
loaf	on table
knife	on table
fridge	in kitchen
loaf	in fridge"""

def environment_future():
    k = kitchen()
    put_in_world(k)

    ta = table()
    put_in(ta, k)

    k = knife()
    put_on(k, ta)

    r = ralph()
    #r.set_color()
    put_in(r, k)


def task_goto_knife(a):
    
    return True


def task_pick_up_knife(a):
    return True
