
#cp COPYING $(SIM_NAME)_$(SIM_VERSION)/
SIM_VERSION=0.4
SIM_NAME=isis_world
tar: *.py
	touch som/test.pyc
	rm */*.pyc
	tar cf simulator-$(SIM_VERSION).tar COPYING simulator.py som models visual xmlrpc lab1_ralph.py lab2_ralph.py
	gzip simulator-$(SIM_VERSION).tar
	scp simulator-$(SIM_VERSION).tar.gz dustin@ml.media.mit.edu:public_html/6.868/

# /Developer/Panda3D/lib/direct/p3d/packp3d.py
#panda3d makescripts/packp3d.p3d

package: main.py
	packp3d -o isis_world.p3d  -d . -r ode -r morepy -e isis -c auto_start=1

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



