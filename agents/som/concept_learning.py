#!/usr/bin/env python
""" 
Tom Mitchell's Version Space learner that works on any data structure that implements 3 generality functions:

 - minimum_generalization(example, is_positive, hypotheses=[default_max_specific_hyp])
 - minimum_specialization(example, is_positive, hypotheses=[default_max_general_hyp])
 - covers(hypothesis, example)

It takes a set of positive/negative example Frames (dictionary) and then learns the generalization boundaries:  a most general and specific frames that include positive examples and exclude negative examples: G, S.

Together, these can be thought of as the 'Critics', with a new example, E, it matches the learned concept iff:  covers(G,E) or covers(S,E)

Doesn't handle noisy examples.

TODO: 
    It doesn't exploit the over_hypotheses order or the generative hypotheses nature of python, and it should:
      ideally, when no hypotheses match data, it should expand hypothesis space.  but this means it'd have to save positive
      and negative examples.  maybe it could just save some (in a queue; or most extreme).
  - Need to prune hypotheses where G is more specific than S, or S is more general than G (ideally during generation)
  - Don't use special functions to generate the most general/specific frame, just have default argument on existing functions
  - Build standalone tree/ontology class
 
Last Revision: 2010-04-17
Created by Dustin Smith (dustin@media.mit.edu) 2010-03-14
Covered by GPL v3
"""
import itertools
from operator import itemgetter
from collections import defaultdict
#import generalizers
from bisect import insort

def is_number(x):
    return isinstance(x,(float,int,long,complex))

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    try:
        next(b,None)
    except:
        b.next()
    return itertools.izip(a, b)


def product(*args, **kwds):
    # this is only part of itertools in python 2.6+
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

class IntervalGenerator():
    """ Interval Generator for hypotheses of numeric values""" 
    MIN_DIFF = 0
    def __init__(self,gap_bias=MIN_DIFF):
        self.values = [] 
        self.in_or_out = {} # 0=negative, 1= positive
        self.gap_bias=gap_bias
        self.contradiction = False

    
    def covers(self, hypothesis, instance):
        if not isinstance(hypothesis,tuple):
            # this is the case where a hypothesis is [] 
            return False
        low,high = hypothesis
        if isinstance(instance,tuple):
            # comparing two hypotheses
            low2,high2 = instance
            if low2 >= low and high2 <= high:
                return True
        else:
            if instance >= low and instance <= high:
                return True
        return False
   
    def try_to_add(self,instance,in_or_out):
        if self.in_or_out.has_key(instance):
            if self.in_or_out[instance] != in_or_out:
                self.contradiction = True
            # don't add twice
        else:
            insort(self.values,instance) # add, in order
            self.in_or_out[instance] = in_or_out # set to true
        
    def minimum_specialization(self, instance, in_or_out, hypothesis=(float("-infinity"),float("infinity"))):
        self.try_to_add(instance,in_or_out)
        if self.contradiction:
            # stop using this frame in the hypothesis
            return []
        elif in_or_out == self.covers(hypothesis, instance):
            # this short-circuits unnecessary hypothesis generation/revision
            # when it is not needed (hypothesis excludes negative, incudes positive)
            return  [hypothesis]
        else:
            gap = 0.1 #self._gap()
            hypotheses = []
            tmp_hyp = [float("-infinity")]
            # if first instance is negative, dont begin with -inf:
            #if len(self.values) > 0 and self.in_or_out[self.values[0]] == 0: tmp_hyp = []
            for item in self.values:
                if self.in_or_out[item] == 1:
                    # item is positive, add it
                    tmp_hyp.append(item)
                else:
                    # item is a negative example 
                    if len(tmp_hyp) != 0:
                        if tmp_hyp[-1] < item-gap:
                            # bookend with item-gap if it's bigger than current end
                            tmp_hyp.append(item-gap)
                        hypotheses.append((tmp_hyp[0],tmp_hyp[-1]))
                        tmp_hyp = [item+gap]
            #if len(self.values) == 0 or self.in_or_out[self.values[-1]] == 1: 
            tmp_hyp.append(float("infinity"))
            if len(tmp_hyp) > 1: # avoid (inf,inf)
                hypotheses.append((tmp_hyp[0],tmp_hyp[-1]))
            print "Specialization hyp", hypotheses, " length =", len(hypotheses)
            return hypotheses


    def minimum_generalization(self, instance, in_or_out, hypothesis=(None,None)):
        self.try_to_add(instance,in_or_out)
        if self.contradiction:
            # stop using this frame in the hypothesis
            return []
        elif in_or_out == self.covers(hypothesis, instance):
            # this short-circuits unnecessary hypothesis generation/revision
            # when it is not needed (hypothesis excludes negative, incudes positive)
            return  [hypothesis]
        else:
            gap =  self._gap()
            hypotheses = []
            tmp_hyp = []
            for item in self.values:
                if self.in_or_out[item] == 1:
                    # item is positive
                    if len(tmp_hyp) == 0 or (item-tmp_hyp[-1]) <= gap:
                        # if there's nothing, or we're in the gap:
                        tmp_hyp.append(item)
                    else:
                        # add previous hyp to done, start new one
                        hypotheses.append((tmp_hyp[0],tmp_hyp[-1]))
                        tmp_hyp = [item]
                else:
                    # item is a negative example
                    if len(tmp_hyp) != 0:
                        hypotheses.append((tmp_hyp[0],tmp_hyp[-1]))
                        tmp_hyp = []
            if len(tmp_hyp) != 0:
                hypotheses.append((tmp_hyp[0],tmp_hyp[-1]))
            if len(hypotheses) > 1:
                return []
            #print "Generalization hypotheses", hypotheses, " length =", len(hypotheses)
            return hypotheses

        

    def _gap(self):
        if len(self.values) >= 2:
            return float(min(map(lambda x: x[1]-x[0], pairwise(self.values))))
        else:
            return 0.1 

def flatten(frame,key=[]):
    """ Takes a dictionary with nested values and then flattens its into a dictionary
    with non-nested values.  Nested keys are joined by "___" delineator that can be
    used to un-flatten the dictionary later"""
    d = []
    for k, v in frame.items():
        if isinstance(v,dict):
            d += flatten(v,key + [k])
        else:
            d.append((key+[k],v))
    if key == []:
        return dict([("___".join(k),v) for k,v in d])
    else:
        return d

def unflatten(frame):
    """Unflattens a dictionary"""
    d = {}
    for key, val in frame.items():
        subkeys = key.split("___")
        d2 = d
        for subkey in subkeys[:-1]:
            if not d2.has_key(subkey): d2[subkey] = {}
            d2 = d2[subkey]
    for key, val in frame.items():
        subkeys = key.split("___")
        d2 = d
        for subkey in subkeys[0:-1]:
            d2 = d2[subkey]
        d2[subkeys[-1]] = val
    return d

class VersionSpaceLearner():
    """ Implements Tom Mitchell's Version-Space learner for conjunctive concept descriptions, instances
    are single frames with many slots.  Hypotheses are both generalizations and specialization boundaries
    of values for slots instances, e.g., for a number value, they are maximum and mininum points;  for a 
    category, they are the most general and most specific categories.  Slot types (types of dictionary 
    attribute values) can be anything that appropriately implement the LearningAttributeInterface. 

    This learning procedure maintains a sets for the boundaries of positive and negative concept descriptions,
    as the most general matches that exclude negative examples, and the most specific hypotheses that
    include positive examples.

    Examples are thrown away after being observed, being made redundant by the training examples.

    Note: this assumes the examples are accurate, i.e., this learning method is not resilient to noise.
    - this also does assumes a generality relationship between all of the values in the arguments,
    most contemporary learning approaches do not assume orderings or bounded thresholds but instead 
    operate on a distance function within some space -- constructed by linear combinations of features
    (in this case, each attribute/value is taken as face value). 

    To upgrade this approach to new learners, new "transformations" of features (including linear 
    combinations) could be introduced and extended from the input variables.


    The result is two boundaries, to be interpreted as: the set of all hypotheses that are between the two
    boundaries.  Any instance is a member of the class if it is covered by a generalization or specialization
    boundary

    """
    def __init__(self, generalization_structures={}, overhypothesis={}, debug=False):
        self.h_gens = [{}]
        self.h_spec = [{'None':(None,None)}] # something that will trigger an error
        self.gs = generalization_structures
        self.oh = defaultdict(int,overhypothesis)
        self.bad_keys = set()
        self.gen_gens = []
        self.spec_gens = []
        self.num_keys = 1
        self.debug = debug # turns on warning messages


    def ordered_keys(self,keys_a,keys_b=[]):
        keys = set(keys_a).union(set(keys_b))
        return sorted(list(keys-self.bad_keys), key=self.oh.__getitem__, reverse=True)[0:self.num_keys]

    def remove_bad_keys(self,instance):
        return dict(filter(lambda x: x[0] not in self.bad_keys, instance.items()))

    def frame_covers(self, hyp, instance):
        # a hypothesis frame "covers" an instance,
        for k, v in self.remove_bad_keys(hyp).items():
            if not instance.has_key(k):
                return False
            if self.gs.has_key(k):
                if not self.gs[k].covers(hyp[k],instance[k]): 
                    return False
            else:
                pass
                #"Skipping key", k, v
              # try to implement using the generic way
        return True
    
    def check_gs_key(self, key, value):
        if not self.gs.has_key(key):
            if is_number(value):
                self.gs[key] = IntervalGenerator()
            else:
                return False
        return True

    def frame_specialization_generator(self, instance, in_or_out, hyp={}):
        # takes a (usually negative) instance and makes hyp in G (not) cover it
        sorted_keys = self.ordered_keys(instance.keys(),hyp.keys())
        sorted_vals = []
        unused_keys = set() # with specialization, we don't want to delete bad keys permanently
        for key in sorted_keys:
            if instance.has_key(key) and not hyp.has_key(key):
                if self.check_gs_key(key,instance[key]):
                    # FIXME: (None,None) should really be pulled from MAX_GENERAL
                    result = self.gs[key].minimum_specialization(instance[key],in_or_out)
                    if result != []:
                        # no contradiction
                        sorted_vals.append(result)
                    else:
                        unused_keys.add(key)
                        sorted_vals.append(None)
                else:
                    unused_keys.add(key)
                    sorted_vals.append(None)
            elif not instance.has_key(key):
                sorted_vals.append([hyp[key]])
            elif self.gs.has_key(key) and in_or_out != self.gs[key].covers(hyp[key],instance[key]):
                result = self.gs[key].minimum_specialization(instance[key],in_or_out,hyp[key])
                if result != []:
                    # no contradiction
                    sorted_vals.append(result)
                else:
                    unused_keys.add(key)
                    sorted_vals.append(None)
            else:
                sorted_vals.append([hyp[key]])
        
        sorted_keys = list(set(self.ordered_keys(instance.keys(),hyp.keys()))-unused_keys)
        for i in product(*filter(None,sorted_vals)):
            #print "Yielding ", dict(zip(sorted_keys,i))
            yield dict(zip(sorted_keys,i))

    def frame_generalization_generator(self, instance, in_or_out, hyp={}):
        # takes a (usually positive) instance and makes hyp in S (not) cover it
        sorted_keys = self.ordered_keys(instance.keys(),hyp.keys())
        sorted_vals = []
        unused_keys = set() 
        for key in sorted_keys:
            if instance.has_key(key) and not hyp.has_key(key):
                # create new minimally generallized key for this:
                if self.check_gs_key(key,instance[key]):
                    result = self.gs[key].minimum_generalization(instance[key],in_or_out)
                    if result != []:
                        # no contradiction
                        sorted_vals.append(result)
                    else:
                        self.bad_keys.add(key)
                        sorted_vals.append(None)
                else:
                    self.bad_keys.add(key)
                    sorted_vals.append(None)
            elif not instance.has_key(key):
                self.bad_keys.add(key)
                sorted_vals.append(None)
            elif self.gs.has_key(key) and in_or_out != self.gs[key].covers(hyp[key],instance[key]):
                result = self.gs[key].minimum_generalization(instance[key],in_or_out,hyp[key])
                if result != []:
                    # no contradiction
                    sorted_vals.append(result)
                else:
                    self.bad_keys.add(key)
                    sorted_vals.append(None)
            else:
                # already covers
                sorted_vals.append([hyp[key]])
        sorted_keys = list(set(self.ordered_keys(instance.keys(),hyp.keys()))-unused_keys)
        for i in product(*filter(None,sorted_vals)):
            yield dict(zip(sorted_keys,i))

    def add_positive_example(self,pos):
        self.add_example(pos,1)

    def add_negative_example(self,neg):
        self.add_example(neg,0)

    def add_example(self, e, in_or_out):
        e = self.remove_bad_keys(flatten(e))
        to_refine = False
        to_spec = True
        for g in self.h_gens:
            #print "General", g, e, self.frame_covers(g,e), in_or_out != self.frame_covers(g, e)
            if in_or_out != self.frame_covers(g, e):
                if self.debug: print "-------- BAD GENERAL ", g,e
                self.h_gens.remove(g)
                to_refine = True
                self.gen_gens.insert(0,self.frame_specialization_generator(e,in_or_out,g))
        for s in self.h_spec:
            #print "Specific", s, e, self.frame_covers(s,e), in_or_out != self.frame_covers(s, e)
            if in_or_out != self.frame_covers(s, e):
                if self.debug: print "-------- BAD SPECIFIC ", s,"\n\n",e 
                self.h_spec.remove(s)
                self.spec_gens.insert(0,self.frame_generalization_generator(e,in_or_out,s))
                to_spec = True
        if len(self.h_spec) == 0 or len(self.h_gens) == 0:
            # when we kill all hypotheses, consider using another key
            self.num_keys += 1
        # add empty generators
        self.spec_gens.append(self.frame_generalization_generator(e,in_or_out))
        self.gen_gens.append(self.frame_specialization_generator(e,in_or_out))
        if to_spec:
            for new_s in itertools.chain(*self.spec_gens):
                if len(self.h_spec) != 0: break
                if self.debug: print "Try new specialization", new_s, e, in_or_out ==self.frame_covers(new_s,e)
                if in_or_out == self.frame_covers(new_s,e):
                    #make sure it's not less specialized
                    most_spec = True
                    for ns in self.h_spec:
                        if self.frame_covers(new_s,ns):
                            #not most specific
                            most_spec = False
                            break
                    if most_spec == False: continue # not most spec, skip
                    if self.debug: print "ADDING NEW SPECIFIC HYPOTHESIS", new_s
                    self.h_spec.append(new_s)
                    break# lazy generation
        if to_refine:
            for new_g in itertools.chain(*self.gen_gens):
                if len(self.h_gens) != 0: break
                if self.debug: print "Try new generalization", new_g, e, in_or_out ==self.frame_covers(new_g,e)
                if in_or_out == self.frame_covers(new_g,e):
                    #make sure it's not less general 
                    most_gen = True
                    for ng in self.h_gens:
                        if self.frame_covers(ng,new_g):
                            #not most general
                            most_gen = False
                            break
                    if most_gen == False: continue
                    if self.debug: print "ADDING NEW GENERAL HYPOTHESIS", new_g
                    self.h_gens.append(new_g)
                    break # lazy generation
          
        self.spec_gens.pop() # remove empty generator 
        self.gen_gens.pop() # remove empty generator


    def print_hypotheses(self):
        print "\n--------------------------"
        print "General Hypotheses:"
        for g in self.h_gens:
            print "\t", unflatten(g)
        print "\nSpecific Hypotheses:"
        for s in self.h_spec:
            print "\t", unflatten(s)

    def in_concept(self, frame):
        """ Valid concepts are covered by *either* a hypothesis in the most general or
        most specific hypotheses."""
        frame = self.remove_bad_keys(flatten(frame))
        gf_num = len(filter(lambda g: self.frame_covers(g, frame), self.h_gens))
        sf_num = len(filter(lambda s: self.frame_covers(s, frame), self.h_spec))
        return gf_num > 0 or sf_num > 0

def test2():
    # FIXME: recent revision broke DAG learning
    tree = Tree()
    tree.add_edge("root","animals")
    tree.add_edge("root","objects")
    tree.add_edge("animals","mammals")
    tree.add_edge("mammals","dogs")
    tree.add_edge("mammals","humans")
    tree.add_edge("animals","insects")
    tree.add_edge("objects","useful")
    tree.add_edge("objects","useless")
    tree.add_edge("useful","computers")
    tree.add_edge("useful","teevees")
    tree.add_edge("useless","ipads")
    vs2 = VersionSpaceLearner(generalization_structures={'j':tree}, overhypothesis={'j':2,'a':3})
    vs2.add_positive_example({ 'j':'dogs'})
    vs2.add_positive_example({ 'j':'mammals'})
    vs2.add_negative_example({ 'j':'ipads'})
    vs2.print_hypotheses()
    for node in tree.nodes():
        #print node, vs.in_concept({'j':node})
        print node, "is in concept?", vs2.in_concept({'j':node, 'a':31})

def test3():
    vs = VersionSpaceLearner()#overhypothesis={'i':2,'a':1})
    vs.add_positive_example({'i':20})
    vs.add_positive_example({'i':22})
    vs.add_negative_example({'i':28})
    vs.add_positive_example({'i':25})
    vs.print_hypotheses()
    for i in range(19,30):
        print i, "is in concept?", vs.in_concept({'i':i})

def test1():
    """ Tests Ralph with actual examples from the  simulator"""
    import frame_utils
    import cPickle
    examples = cPickle.load(open('../examples.pickle','r'))
    #vs = VersionSpaceLearner(overhypothesis={'objects___piece_of_toast___distance':25})#
    vs = VersionSpaceLearner()
    #generalization_structures={'j':tree}, overhypothesis={'j':2,'a':3})
    num_e = 106 
    for in_or_out, e in examples[0:num_e]:
        print "PREDICTION", vs.in_concept(e)
        vs.add_example(e,in_or_out)
        #print "\n\nKeys", vs.ordered_keys(flatten(pos))
    #print "\n\nKeys", vs.ordered_keys(neg)
    vs.print_hypotheses()


def test4():
    vs = VersionSpaceLearner(debug=False)
    examples = [[0, {'a': 3.0}],\
                [1, {'a': 5.0, 'b': 10.0}],\
                [1, {'b': 20.0}]]
    for pos,e in examples:
        print "Added example",e
        vs.add_example(e,pos)
    vs.print_hypotheses()
    print "Bad keys", vs.bad_keys
    vs = VersionSpaceLearner(debug=False)
    examples = [[0, {'a': 3.0}],\
                [1, {'a': 5.0, 'b': {'c': 10.0}}],\
                [0, {'b': 20.0}]]
    for pos,e in examples:
        print "Added example",e
        vs.add_example(e,pos)
    vs.print_hypotheses()
    print "Bad keys", vs.bad_keys
    #vs.print_hypotheses()

if __name__ == "__main__":
    from frame_utils import *
    from random import *
    test4()
    
