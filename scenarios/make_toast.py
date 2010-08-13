self.description = "making toast in isisworld"

def environment("first"):
    
    k = kitchen()
    r = ralph()
    r.color = "blue"
    
    r.set_color()
    k.put_in(r)
    t = toast()
    ta = table()
    put_on(t,ta)


def task("go to toast"):
    # define which environment to use (if not the default)
    task.environment = "first"
    
    def train():
        putin(ralph,kitchen)

    def goal("ralph's at the toast")
        return ralph.in_view("toast")
        r.in_view(t)
