scenario.description = "picking up a knife"
scenario.author = "dustin smith"
scenario.version = "1"

def environment():
    k = kitchen()
    put_in_world(k)

    ta = table()
    put_in(ta, k)

    k = knife()
    put_on(k, ta)

    r = Ralph("susan")
    #r.set_color()
    put_in(r, k)
    
    # required at the end of the environment setup
    store(locals())


def task_goto_knife(a):
    
    return True


def task_pick_up_knife(a):
    return True
