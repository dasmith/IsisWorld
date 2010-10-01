from pandac.PandaModules import BitMask32
from constraint import *


bitMaskTest = {
        'generalKCC': {'collides': ['environment','container','pickable'], 'exclude': ['kccEnvCheckerRay']},
        'container': {'collides': ['generallKCC','environment'], 'exclude': ['pickable']},
        'environment': {'collides': ['container','generallKCC','environment','kccEnvCheckerRay'], 'exclude': ['aimRay']},
        'kccEnvCheckerRay': {'collides': ['container','environment','pickable'], 'exclude': ['generalKCC']},
        'pickable': {'collides': ['environment','kccEnvCheckerRay','aimRay','generallKCC','pickable'], 'exclude': ['container']},
        'aimRay': {'collides': ['container','kccEnvCheckerRay','pickable'], 'exclude': ['generalKCC','environment']},
}

import random
p = Problem()
keys = bitMaskTest.keys()
random.shuffle(keys)
for k in keys:
    p.addVariable(k,range(0,8))
    p.addVariable(k+'cat',range(0,8))
    
def collides(a,b,acat,bcat):

    return (BitMask32(acat) & BitMask32(b)) | (BitMask32(bcat) & BitMask32(a)) != BitMask32(0)

p.addConstraint(lambda a,b,c,d: collides(a,b,c,d), ['pickable','pickable','pickablecat','pickablecat'])
 
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
                    p.addConstraint(lambda a,b,c,d: collides(a,b,c,d), [bm,bm2,bm+"cat",bm2+"cat"])
            elif bm in exc2 or bm2 in exc:
                if bm in col2 or bm2 in col:
                    print "CONTRADICTION", bm, bm2
                else:
                    p.addConstraint(lambda a,b,c,d: not collides(a,b,c,d), [bm,bm2,bm+"cat",bm2+"cat"])
                                                   
solution = p.getSolution()

print "\nbitMaskDict = {"
for k, v in solution.items():
    if k[-3:] == "cat": continue
    print '            "%s" : (BitMask32(%i), BitMask32(%i)),' % (k,v,solution[k+"cat"])
print "}\n"