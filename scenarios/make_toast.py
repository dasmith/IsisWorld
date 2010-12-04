from src.isis_scenario import IsisScenario

class Scenario(IsisScenario):
    
    description = "making toast in isisworld"
    author = "dustin smith"
    version = "1"

    def environment():
        k = kitchen(length=15, width=15, height=10)
        put_in_world(k)

        
        f = fridge()
        put_in(f, k)

        b = butter()
        put_in(b, f)

        ta = table(scale=7)
        put_in(ta, k)

        ta2 = table(scale=7)
        put_in(ta2, k)

        ta3 = table(scale=8)
        put_in(ta3, k)

        ta4 = table(scale=7)
        ta4.scale = 1
        put_in(ta4, k)

        t = toaster()
        put_on(t, ta)
        
        kn = knife()
        put_on(kn, ta)

        # adding the oven
        ov = oven()
        put_in(ov, k)
    
        l = loaf()
        put_in(l, f)
        
        l = loaf()
        put_on(l, ta2)

        ralph = IsisAgent("Ralph")
        
        lauren = IsisAgent("Lauren")

        put_in_world(lauren)
        put_in_front_of(ralph,f)

        # required at the end of the environment setup
        store(locals())


    def task_toaster_in_view():
        #name = "toaster is in view"
        # define which environment to use (if not the default)
        #environment = "first"

        def train():
            k.put_in(r) # put ralph in the kitchen

        def goal_toaster_in_view():
            return ralph.in_view(t)

        store(locals())
