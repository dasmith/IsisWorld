description = "making toast in isisworld"
author = "dustin smith"
version = "1"

def environment():
    k = kitchen()
    r = ralph()
    #r.set_color()
    k.put_in(r)
    t = toast()
    ta = table()
    ta.put_on(t)


def task_toast_in_view():
    task.name = "toast in view"
    # define which environment to use (if not the default)
    task.environment = "first"
    
    def train():
        k.put_in(r) # put ralph in the kitchen

    def goal():
        goal.name = "toast in view"
        return r.in_view(t)
