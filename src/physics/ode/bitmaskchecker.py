from pandac.PandaModules import BitMask32
from constraint import *


bitMaskTest = {
        'generalKCC': {'collides': ['environment','container','pickable'], 'exclude': ['kccEnvCheckerRay']},
        'container': {'collides': ['generallKCC','environment'], 'exclude': ['pickable']},
        'environment': {'collides': ['container','generallKCC','environment','kccEnvCheckerRay'], 'exclude': []},
        'kccEnvCheckerRay': {'collides': ['container','environment','pickable'], 'exclude': ['generalKCC']},
        'pickable': {'collides': ['environment','kccEnvCheckerRay','aimRay'], 'exclude': ['container']},
        'aimRay': {'collides': ['container','environment','kccEnvCheckerRay','pickable'], 'exclude': ['generalKCC']},
}

import random
p = Problem()
keys = bitMaskTest.keys()
random.shuffle(keys)
for k in keys:
    p.addVariable(k,range(0,31))
   # p.addVariable(k+'cat',range(0,31))
    
def collides(a,b):
    return ((BitMask32(a) & BitMask32(b)) | BitMask32(a) & BitMask32(b)) == BitMask32.bit(0)# | (BitMask32(acat) & (BitMask32(bcat)))) != BitMask32.bit(0)

for bm, d in bitMaskTest.items():
    for bm2, d2  in bitMaskTest.items():
        col = d['collides']
        exc = d['exclude']
        if bm != bm2:
            col2 = d2['collides']
            exc2 = d2['exclude']
            if bm in col2 or bm2 in col:
                if bm in exc2 or bm2 in exc:
                    print "CONTRADICTION", bm, bm2
                else:
                    p.addConstraint(lambda a,b: collides(a,b), [bm,bm2])
            elif bm in exc2 or bm2 in exc:
                if bm in col2 or bm2 in col:
                    print "CONTRADICTION", bm, bm2
                else:
                    p.addConstraint(lambda a,b: not collides(a,b), [bm,bm2])
                                                   
print p.getSolution()

