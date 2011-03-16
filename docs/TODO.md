

# To Do List
 
  - build tool for normalizing the position and rotations for objects.
  - Loading and running [IsisScenarios](#IsisScenarios) files:
    - buttons for starting a task, running a training and test scenario
    - recording statistics about the task: how many steps since it started, state of task (failed/completed/ongoing)
    - displaying state of task in the menu
  - documenting a skeleton generator file with all possible superclass attributes, so that other people can work on the project by adding / describing models.
  - separating actions from the `main.py` as a different data structure in a different file.
  - IsisEvent class
  - Storing and resuming game states
  - UI overhaul: clean up, make UI much more thin.
  - re-write layout managers
  - UI triggered exit should first kill xmlrpc (and join thread?) before shutting down
  - save screenshots in relative path (same relative path as scenarios dir)
  
## Has Been Done List

Here's the list of changes that have been made since the last version:

  - fixed problem of dynamically loading scenario files in panda3d packages. new distributions available!
  - specifying scale ranges for some of the common models sizes, the same way the size of the kitchen is chosen from a random range.
  - in isis_agent:pick_object_up_with, special handling for objects on surfaces and objects in containers: Items being removed from containers first have their parent checked to see if `is_open` is True. If it is not, then the pickup action fails.  Objects like the toaster, have `is_open` as a hidden property, that is turned to `False` iff the toaster `is_on`.
  - creation of `IsisAttribute` with consistency checks.
  - scenario files allow defaults to be specified as keyword arguments. `k = kitchen(width=10, height=7)`
  - objects can have "front" orientation that is used to place objects around a room, with their backs to the wall
  - checking for whether the goal state is met
  - migrating the `kitchen.isis` into an "scene initialization" section of the "scenario/" files.
  - a DirectGUI for loading tasks, which is the default screen when the simulator loads.
  - recording state of task/scenario in logging file
  - exporting screen shots
  - RoomLayout layout manager that puts objects around the walls
