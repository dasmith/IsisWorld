# Isis World Simulator


# To do in simulator

1. Physical Motion Class
 - rotation and translation, w.r.t, velocities

2. picture in picture to see ralph's visual frame

3. action primitives to impolement:
 -  Look up/down/left/right
 - use x with y
 - drop (stop pick up)
 - pick up
 - sense
   - add to senses: location in frustrum (x,y) 

4. Step simulator action
 - move objects down if not on other objects
 - physics does next thing on queue (sequential list of things to do)
 - walk to

# Improvements for the simulator

- general module for loading components
  - representing spatial relations of containment (in) and surface contact (on)
  - allowing objects to be nested
  - generative parameter ranges (perhaps a distribution) to accommodate variance 
  - configuration files?

- replace ralph with nicer-looking model
- obtain copyright information for all models (remove on open source models)

- quick way to author events and state-changes
  - perhaps using domain specfic language (or simplified english -- allowing use of OMICS corpus)
 

## Vision
- consult with Pinto about 'vision' perceptual slot


## Multi-client
- experiment with builtin connection libraries
- multiplayer/agent (use Panda3D libraries along with server)


# Improvements for agent

## Sharing memory between critics
 - way to describe perceptions in abstract domain (current perceptual frame is pretty abstract: it already has objects)
 - way to pass references to between mental resources -- so they can be chained and used together
 - decentralized detection of whether a critic goes on or off?

# Improvements for Learning system

 - use intervaltree (could be list, as long as they are non-overlapping) to represent ranges of numeric values.  Right now, it (slightly uselessly) only recognizes a _larger_ number as a generalization of another. It can only find valid hypotheses **if all negative examples have numeric values that are strictly less than the lowest positive example's value**.  This is unrealistic, and we could represent numeric values as conjunctions of intervals (most general being (-inf,inf), of which there are infinite specializations -- requiring working: 
 - lazy hypothesis generation.  This is currently implemented, but was omitted because sometimes the first generated working hypotheses is invalidated by a second example.  
 - generalize to work with dictionaries (recursive structures)

 

