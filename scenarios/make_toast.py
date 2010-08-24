description = "making toast in isisworld"
author = "dustin smith"
version = "1"

environment = """kitchen	at 0,0,0
table	in kitchen
toaster	on table
loaf	on table
knife	on table
fridge	in kitchen
loaf	in fridge"""


def environment_future():
    k = kitchen()
    put_in_world(k)

    ta = table()
    put_in(ta, k)

    t = toaster()
    put_on(t, ta)

    k = knife()
    put_on(k, ta)

    f = fridge()
    put_in(f, k)

    l = loaf()
    put_in(l, f)

    r = ralph()
    #r.set_color()
    put_in(r, k)

def task_toast_in_view():
    task.name = "toast in view"
    # define which environment to use (if not the default)
    task.environment = "first"
    
    def train():
        k.put_in(r) # put ralph in the kitchen

    def goal():
        goal.name = "toast in view"
        return r.in_view(t)
