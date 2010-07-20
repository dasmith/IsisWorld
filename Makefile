
#cp COPYING $(SIM_NAME)_$(SIM_VERSION)/
SIM_VERSION=0.4
# /Developer/Panda3D/lib/direct/p3d/packp3d.py
#panda3d makescripts/packp3d.p3d

make: main.py
	ipython -pdb main.py


clean: 
	rm -rf **/*.pyc *.pyo; **/*.pyo

package: main.py
	packpanda -i build isisworld.pdef

panda: *.p3d
	rm *.p3d
	wget http://runtime.panda3d.org/packp3d.p3d
	wget http://runtime.panda3d.org/pdeploy.p3d

build: package 
	echo "Packaging isis_world.p3d"
	pdeploy -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -a "edu.mmp"  -l "GPL v3" -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -s isis_world.p3d standalone 

install: package 
	echo "Packaging isis_world.p3d"
	pdeploy -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -l "GPL v3" -P osx_i386 -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -s isis_world.p3d installer 

mac2:
	packp3d -o isis_world.p3d  -d . -r ode -r morepy -e isis -e isis
	pdeploy -N "IsisWorld" -v 0.5 isis_world.p3d installer

mac:
	panda3d packp3d.p3d -o isis_world.p3d  -d . -r ode -r morepy -e isis -e isis
	rm -rf ~/Library/Caches/Panda3d/
	rm -rf osx_i386
	panda3d pdeploy.p3d -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -l "GPL v3" -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -P osx_i386 -s isis_world.p3d standalone 

deploy: build
	echo "Making cross-platform builds and uploading them"
	for arg in linux_amd64 linux_i386 osx_i386 osx_ppc win32; do\
		rm -rf $(SIM_NAME)_$(SIM_VERSION); mkdir $(SIM_NAME)_$(SIM_VERSION) ;\
	      	echo mv $$arg/* $(SIM_NAME)_$(SIM_VERSION) ;\
	      	mv $$arg/* $(SIM_NAME)_$(SIM_VERSION) ;\
		tar cf $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar $(SIM_NAME)_$(SIM_VERSION) ;\
		gzip $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar ;\
		mv $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar.gz builds/ ; \
		done
	rsync -a builds dustin@ml.media.mit.edu:public_html/6.868/



