#!/bin/env python
# Frame Utility Library
#  - 2010-03-09  First edition.  dustin@media.mit.edu

NULL_TRANSFRAME = {'added': {}, 'changed': {}, 'removed': {}}

def create_transframe(frame_a,frame_b):
    """ Takes two frames (aka: dictionaries, hash functions, trees) and computes their differences, an asymmetric operation, showing what needs to be done to convert A to B, in terms of additions, removals and changes.
      Returns array of difference tuples, of types:
          added keys - present in B that are not present in A
          removed keys - present in A that are not present in B
          changed keys - present in both A and B that have had a value changed in B (computes difference)
          [ recusive call for edges to sub-frames  with same name ]
   
      Syntax:
       {'type_of_difference': { (path, to, node, from, root) : {'key1' : 'val_or_diff_1'}}

      Assumptions: 1) Frames contain only values that have '__sub__' (subtraction) and '__eq__' (equality) operators
                      defined.   
                   2) structures with arity greater than 1 need to be dictionaries. 
                       'key': 1   # YES
                       'key':[1,2]  # NO! 
                       'key': {'sub-key': 1, 'another-sub-key': 2}  # YES 
    
      Designed to work with the same data structure it returns, e.g.  differences of differences
    """
    results={'added': {}, 'removed': {}, 'changed': {}}

    def get_diff_internal(level,a,b):
        a_keys = a.keys()
        b_keys = b.keys()
        for k in set(b_keys).difference(set(a_keys)):
            if not results['added'].has_key(level): results['added'][level] = {}
            results['added'][level][k] = b[k]
        for k in set(a_keys).difference(set(b_keys)):
            if not results['removed'].has_key(level): results['removed'][level] = {}
            results['removed'][level][k] = a[k]
        same  = set(a_keys).intersection(set(b_keys))
        # FIXME: have it do something different when 
        # values cannot be subtracted (different actions for different data structures)
        subdicts =[]
        for k in same:
            #print "K = ", k, "a[k] ", a[k], "b[k]", b[k]
            if a[k].__class__ == b[k].__class__ and not isinstance(a[k],dict) and a[k] != b[k]:
                if not results['changed'].has_key(level): results['changed'][level] = {}
                if isinstance(a[k],list):
                    results['changed'][level][k] = [x for x in b[k] if x not in a[k]]
                else:
                    results['changed'][level][k] = a[k]-b[k]
            elif isinstance(a[k],dict) and b[k].__class__==a[k].__class__:
                subdicts.append(k)
        return [(s,a[s],b[s]) for s in subdicts]

    sd = [((), frame_a, frame_b)]
    while sd:
       # iterate through subdictionaries and keep calling 
       n = sd.pop()
       sd += get_diff_internal(n[0],n[1],n[2])
    return results
                        

def apply_transframe_to_frame(frame, tframe):
    """ Takes a frame and applies difference frame (transframe) to construct new frame"""
    for edit in ['added', 'removed', 'changed']:
        for path, vals in tframe[edit].items():
            tmp = frame
            for subnode in path:
                if not frame.has_key(subnode):
                    frame[subnode] = {}
                tmp = frame[subnode]
            for k, v in vals.items():
                if edit == 'added':
                    tmp[k]=v
                elif edit == 'changed':
                    # handle lists
                    tmp[k]=v
                elif edit == 'removed':
                    tmp.__delitem__(k)
    return frame



if __name__ == '__main__':
    # tests
    a = {'a':2,'b':3,'c':{'dog':[3]}}
    b = {'a':1,'b':3,'c':{'dog':[3,4],'seahorse':2}}
    c = {'c':3}
    d = {'left':3}
    e = {'left':4}
    f = {'left':6}
    print "\n\nTest 1: Differences:\n"
    print create_transframe(a,b)
    print create_transframe(b,c)

    print "\n\nTest 2: Reconstruction:\n"
    diff = create_transframe(a,b)
    print apply_transframe_to_frame(a,diff)
    
    print "\n\nTest 3: Differences of Differences:\n"
    print create_transframe(create_transframe(d,e),create_transframe(e,f))


