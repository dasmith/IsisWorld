
def task1(a):
    a.worldDescription = """table in kitchen
    bread in table
    """
    
    task1 = IsisTask("pick up toast", order=1)
    task1.setGoal("")
    
    a.addTask(task1)


def task2(a):
    print "task2"