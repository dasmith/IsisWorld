# Isis World Simulator

The IsisWorld simulator is available to researchers for building and evaluating problem solving and language learning systems with everyday problems that take place in a kitchen (on a campground?  house coming soon!).  Some documentation and arguments about theoretical underpinnings aimed toward the metareasoning community are available in this paper: 
 
   * [An open source commonsense simulator for AI researchers](http://web.media.mit.edu/~dustin/simulator_metacog_@ai_2010.pdf).  Dustin Smith and Bo Morgan.  *Submitted to AAAI-10 Workshop on Metacognition*.
    
## Improvements for the simulator

 - rotation and translation, w.r.t, velocities
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
 - lazy hypothesis generation.  This is currently implemented, but was omitted because sometimes the first generated working hypotheses is invalidated by a second example.  
 - generalize to work with dictionaries (recursive structures)

 

