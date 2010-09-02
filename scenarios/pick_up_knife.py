scenario.description = "picking up a knife"
scenario.author = "dustin smith"
scenario.version = "1"

def environment():
    k = kitchen()
    put_in_world(k)

    ta = table()
    put_in(ta, k)

    kn = knife()
    put_on(kn, ta)

    r = IsisAgent("Ralph")
    #r.set_color()
    put_in_world(r)
    
    # required at the end of the environment setup
    store(locals())


def task_goto_knife():
    task.name = "go to knife"
    
    def goal():
        return True


def task_pick_up_knife():
    task.name = "pick up knife"
    
    def goal():
        if task.time > 10: return True
