from src.isis_scenario import IsisScenario

class Scenario(IsisScenario):

    description = "picking up a knife"
    author = "dustin smith"
    version = "1"

    def environment():
        k = kitchen()
        put_in_world(k)
        ta = table()
        put_in(ta, k)
        kn = knife()
        put_on(kn, ta)
        kn2 = knife()
        r = IsisAgent("Ralph", position=(0,3,2))
        r.put_in_right_hand(kn2)

        put_in_world(r)
    
        # required at the end of the environment setup
        store(locals())


    def task_goto_knife():
        task.name = "go to knife"

        def goal_try():
            return True
        store(locals())

    def task_pick_up_knife():
        task.name = "pick up knife"

        def goal_try():
            return True
            if task.time > 10: return True

        store(locals())
