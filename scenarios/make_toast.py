scenario.description = "making toast in isisworld"
scenario.author = "dustin smith"
scenario.version = "1"


def environment():
    k = kitchen()
    put_in_world(k)

    f = fridge()
    put_in(f, k)


    ta = table()
    put_in(ta, k)

    t = toaster()
    put_on(t, ta)

    k = knife()
    put_on(k, ta)


    l = loaf()
    put_in(l, f)

    ralph = IsisAgent("Ralph")
    lauren = IsisAgent("Lauren")
    #r.set_color()
    put_in(ralph,k)
    put_in(lauren,k)

    # required at the end of the environment setup
    store(locals())

def task_toast_in_view():
    task.name = "toast is in view"
    # define which environment to use (if not the default)
    task.environment = "first"
    
    def train():
        k.put_in(r) # put ralph in the kitchen

    def goal():
        goal.name = "toast in view"
        return r.in_view(t)
