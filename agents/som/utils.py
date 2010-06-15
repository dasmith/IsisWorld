# colorful debugging
def dprint(name, add_msg=""):
    if len(name.split("__")) > 2:
           kind,level,message = name.split("__")[0:3]
    else:
           kind = "UNK"
           level = "UNK"
           message = name
    CLEAR = '\033[0m' 
    TITLE = {'critic': 'C', 'diffeng':'DE', 'selector': 'S'}
    if TITLE.has_key(kind):
        kind = TITLE[kind]
    if level == 'react':
        COLOR = '\033[94m' # blue
    elif level == 'delib':
        COLOR= '\033[92m' #green
    elif level == 'reflect':
        COLOR = '\033[93m'
    else:
        COLOR = '\033[95m'

    print "%s %s %s %s" % (COLOR,kind,add_msg+" "+message,CLEAR)


def contains_any(str, set):
    """ Check whether sequence str contains ANY of the items in set. """ 
    return 1 in [c in str for c in set]

def contains_all(str, set):
    """ Check whether sequence str contains ALL of the items in set. """ 
    return 0 not in [c in str for c in set]

class compose:
    '''compose functions. compose(f,g,x...)(y...) = f(g(y...),x...))''' 
    def __init__(self, f, g, *args, **kwargs):
        self.f = f
        self.g = g
        self.pending = args[:]
        self.kwargs = kwargs.copy(  )

    def __call__(self, *args, **kwargs):
        return self.f(self.g(*args, **kwargs), *self.pending, **self.kwargs)

class mcompose(compose): 
    '''compose functions. mcompose(f,g,x...)(y...) = f(*g(y...),x...))''' 
    TupleType = type((  )) 

    def __call__(self, *args, **kwargs): 
        mid = self.g(*args, **kwargs) 
        if isinstance(mid, self.TupleType): 
            return self.f(*(mid + self.pending), **self.kwargs) 
        return self.f(mid, *self.pending, **self.kwargs) 
