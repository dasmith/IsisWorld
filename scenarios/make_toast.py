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

    ta2 = table()
    put_in(ta2, k)

    ta3 = table()
    put_in(ta3, k)

    ta4 = table()
    put_in(ta4, k)

    t = toaster()
    put_on(t, ta2)

    kn = knife()
    put_on(kn, ta)

    lf = toaster()
    put_in_world(lf)
    
    l = loaf()
    put_in(l, f)

    l = loaf()
    put_on(l, ta3)

    # adding the oven
    # doesn't appear to have shown up in the world
    ov = oven()
    put_in(ov, k)

    ralph = IsisAgent("Ralph")
    lauren = IsisAgent("Lauren")
    lauren2 = IsisAgent("Lauren2")
    #r.set_color()
    #put_in_world(ralph)
    put_in_world(lauren2)
    put_in_world(lauren)
    put_in_front_of(ralph,kn)

    # required at the end of the environment setup
    store(locals())


def task_toaster_in_view():
    task.name = "toaster is in view"
    # define which environment to use (if not the default)
    task.environment = "first"

    def train():
        k.put_in(r) # put ralph in the kitchen

    def goal_toaster_in_view():
        return ralph.in_view(t)

    store(locals())
