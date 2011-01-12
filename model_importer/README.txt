Description:
    This script is a wrapper around the egg-optchar executable that
comes with the Panda3D library. egg-optchar's function is to make
modifications to .egg files (scaling, transforming, rotating, and
similar actions). This allows correction of models that are
inappropriately positioned/scaled for the simulation they are being used
in. egg-optchar is a command-line tool, which isn't optimal for making
adjustments to 3D graphics, so this script aims to make the task a bit
easier.
    In its current form, the script displays a .egg model in a viewing
window, and provides a text field in which the user can provide
arguments to egg-optchar. The script then runs egg-optchar with those
arguments on the model being displayed, and refreshes the model to show
how it changed.

How to Use:
    Go to a shell, and cd to the directory that viewer.py is in. Then type
    python viewer.py /full/path/to/model 
If no model is provided as an argument, the script defaults to a
modified copy of a panda model that is in the same directory. 

NOTE: To make the default model selection work, you will need to update
the line
modelName = "/c//Users/Rahul_2/Documents/IsisWorldUROP/egg_optchar_wrapper/pandaModCopy.egg"
with the appropriate information of your own directory structure.

    The script will then display a window with models/environment as the
background and your chosen model in the display. (If your model is much
smaller or much bigger than the environment it may not be visible unless
you egg-optchar it to scale it first) There are currently 2 GUI
elements:
1. A button that refreshes the model when you click on it.
2. A text field where you can input arguments to egg-optchar.
Example: Suppose you want to scale the model by a factor of 2.
         This is done by typing -TS 2 into the text field and hitting
         Enter. The script will then construct the following command:
         egg-optchar -o <modelName> -TS 2 <modelName> and call it.
         It will then refresh the model to show you the changed version.
    Note that you do not need to type "egg-optchar" or the model
name; the script does that for you. Currently all changes are
done immediately to the same model and can not be undone
(though you can scale/rotate/translate the model by the inverse
value of the initial change)

Future Changes to Make:
1. Features
  - Right now this script only modifies the given model inplace, it
    might be useful to allow the user to specify an -o <file>
  - It might also be helpful to save a temporary model, change that
    model, and allow the user to confirm that they want the changes to
    be permanent (upon which the original model can be changed)
  - Display multiple models so the user can compare them (right now you
    could do this by running multiple instances of this script)
  - Allow the user to specify the background. (e.g. for IsisWorld the
    kitchen might be more appropriate than the "generic" background)
2. Interface
  - Reposition the buttons so they're a bit more conveniently placed
  - Possibly add GUI elements to adjust the model; then the user
    wouldn't have to learn how to pass arguments to egg-optchar (but
    still keep the text input for those who prefer it)
Right now this isn't much more than a prototype, suggestions for changes
would be welcomed!
