% A Roadmap to AI

*This page contains a collection of characterizations of problem domains.  The list of problems become progressively more difficult.*


IsisWorld to simulate everyday commonsense reasoning problems that span many realms, such as the social, visual, kinesthetic, physical, spatial and mental.  These are precisely the kinds of "integrative AI" problems that require a systems approach and pull from many of the subfields.

What is a problem "realm"?  Consider the problem of *hailing a taxi*.  You could represent and reason about this problem in several different ways.

 1. **Temporally**: Wait for a taxi. Maybe if you stay put, a taxi will drive by
 2. **Spatially**:  Find a taxi. You must eliminate the distance between yourself and a taxi.
 2. **Socially**: Call a taxi.  Communicate your position to a dispatching agent and an available taxi will come to you. 

It is this resourcefulness---having many ways to solve a problem---that allows human problem solvers to flexibly adapt to many problem solving situations.  A system that lacks these abilities is *brittle*.

Further, we are looking for test bed to study the problems of meta-reasoning: where a super-level planning system reasons about the world of a sub-planning system.  Returning to a taxi example, we could consider the failure mode which causes a meta-level reasoner to step in and change the state of the planner.  For example, it could ask the system to *elevate* the problem description to pursue the parent goal:  *instead of "searching for a taxi" reconsider the problem as "traveling to your destination" and pursue other options: e.g., walking, train, asking a friend etc*.



## Use cases / Problem Scenarios

The development of the simulator is focused on the following  test scenarios

### 1. Toast Making: studying first-level planning

Ralph is in the kitchen and has the goals of making and eating toast.  Ralph has to "use" the knife to cut the bread, and then put the bread in the toaster. Problems addressed [[#1](http://web.media.mit.edu/~push/Push.Phd.Proposal.pdf)]:
  
  * Bodily, what actions does Ralph have available?
  * Functional, how objects states can change: the effects of actions upon them and how they affect each other.
  * Spatially, navigating through space without bumping into objects
  * Motor routines:  what macro actions can be represented to coordinate common sequences of primitive actions?
  * Self models: how does the situation of Ralph's model (e.g., location of limbs in space, objects in hand, eyes opened or closed) influence the functions of actions he can perform.
  * Visual:  what objects are in the environment, how far are they, what shape and texture do they have?
  * Mental debugging: if all toast-making problem solvers reach impasses, Ralph could reflect on his problem and pop up to his higher goal.

### 2. Knife sharing: studying social interactions

Ralph and his mother Sue are in the kitchen.  Sue is currently using the only knife.  Ralph has to ask Sue to use the knife.  If he grabs the knife from her hand, he will be cut.

  * Mental: what is Sue's active goal ("intention"), does she have the same intention? how will she react to my actions? 
  * Social representations, from [[#1](http://web.media.mit.edu/~push/Push.Phd.Proposal.pdf)]
     - Social networks: who knows who?  who has interacted with whom?
     - Dominance: who sets the goals of this group?  who to listen to?
     - Goal interactions: do my actions help or hinder others?  Who might interfere with my goals?
     - Impriming: can they do something I can't?  what can I learn from them?
     - Groups: what are the roles in this group?  What are the functions of these roles?


### 3. Learning by observation

Sue is communicating a new sequence of actions.  Ralph must identify Sue's plan and then recognize her goal as different, and then learn the new plan as some deviation of the existing plan (e.g., making toast with jelly)
  
  * Plan and goal recognition
  * Planning and debugging in simulated mental worlds

### 4. Imprimer learning

Sue is teaching Ralph how *not* to use a kitchen.  He must learn that the faucet must be turned off after being used, doors closed after they are opened, not to leave the refrigerator open for more time than necessary, etc.  He must learn these how to represent and pursue these imagined goals and antigoals of his imprimer.   This must cover the problem of **shared attention**, where the teacher deliberately acts a certain way to encourage the learner to focus on a relevant aspect of the shared situation.

  * Shared attention and shared models of inference:  "What will Sue think if she sees the mess on the floor?"

### 5. Language learning and instruction execution

Learning the labels of objects from examples. Learning to label events/actions with verb phrases at different temporal resolutions.  Learning how to use and resolve pronouns, the linguistic equivalent of pointing.   Learning the proper sequence to carry out a sequence of actions from a linguistic description

  - learning and representing labels for things (nouns) in the world ("toast")
  - learning and representing adjectives ("black", "hot", "large") -- re-representing items in a perceptual measure space (concept domain) and using adjectives evoke discriminative boundaries with respect to a shared world model.
  - learning and representing composition of linguistic concepts (e.g., "red" in "red wine" is different than "red hair") or the linking constraints between verbs and nouns ("run" + "dishwasher" versus "run" + "marathon")
  - semantic parsing of a sentence into possible "interpretations"
  - interpreting verbs as states or actions (e.g., modeling the taxonomic organization of verbs and how they map to between sets of events, related by generality relationships)
  - interpreting nouns as constituents of states or actions (e.g., modeling the taxonomic organization of nouns and how they map to generality relationships between sets of items)
  - interpreting prepositions by representing items in a visual geometry / using spatial relationships
  - metaphoric mappings between concepts and spatial relationships w.r.t. some decision making process.
  - articulating an event that Ralph has completed with respect to a set of planning decisions, modulated by Ralph's model of the listener's knowledge
  - using hierarchical structure of linguistic phrases and aspectual connectives to model relationships between events and control structure of planning (do X "during", "after", "while" doing Y)
  - language parsing using a cognitively plausible model (e.g., Shift-Reduce parsing) 


### 6.  Communicating instructions

Ralph describes his actions or Sue's actions as an English verb phrase.