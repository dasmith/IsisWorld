window-title "IsisWorld"
window-type onscreen

load-display pandagl
aux-display pandadx9
aux-display pandadx8
#aux-display tinydisplay

usync-video 0
win-size 800 600
clock-mode limited
clock-frame-rate 20 
basic-shaders-only #f
#audio-library-name p3fmod_audio

model-path $MAIN_DIR/media/
model-path /media/
model-path $MAIN_DIR/media/models/
model-path /media/models/
model-path $MAIN_DIR/media/textures/
model-path /media/textures/
model-path $MAIN_DIR/media/music/
model-path /media/music/
model-path $MAIN_DIR/media/fonts/
model-path /media/fonts/

textures-auto-power-2 #t
textures-power-2 none 

text-pixels-per-unit 60

multisamples 2
