
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

package: simulator.py
	packp3d -o isis_world.p3d  -d . -D -r ode -r morepy -m simulator.py -e isis -e py -p xmlrpc -p shaders -p models -p models3 -p textures -p simulator -p som -c auto_start=1


build: 
	echo "Packaging isis_world.p3d"
	python /Developer/Panda3D/lib/direct/p3d/pdeploy.py -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -l "GPL v3" -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -s isis_world.p3d standalone 

mac:
	python /Developer/Panda3D/lib/direct/p3d/pdeploy.py -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -l "GPL v3" -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -P osx_i386 -s isis_world.p3d standalone 

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



