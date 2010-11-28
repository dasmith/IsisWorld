
p3d:
	wget http://runtime-dev.panda3d.org/ppackage.p3d
	wget http://runtime-dev.panda3d.org/packp3d.p3d
	wget http://runtime-dev.panda3d.org/pdeploy.p3d
	panda3d ppackage.p3d -i . testbuild.pdef
	panda3d pdeploy.p3d -i . testbuild.pdef

package:
	panda3d ppackage.p3d -i . testbuild.pdef
	panda3d pdeploy.p3d -N "IsisWorld" -n testbuild -t width=800 -t height=600 -P osx_i386 -v $(SIM_VERSION) tb.p3d standalone

package2:
	ppackage -i . testbuild.pdef
	pdeploy -N "IsisWorld" -v $(SIM_VERSION) tb.p3d standalone

package3:
	panda3d ppackage.p3d -D -i . testbuild.pdef
	panda3d pdeploy.p3d -N "IsisWorld" -n tb -t width=800 -t height=600 -P osx_i386 -v $(SIM_VERSION) tb.p3d standalone
	tar cf tb.tar tb.p3d

profile:
	python -m cProfile -o stats.prof main.py
	# then run runsnake stats.prof

build: package 
	echo "Packaging isis_world.p3d"
	pdeploy -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -a "edu.mmp"  -l "GPL v3" -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -s isis_world.p3d standalone 

install: package 
	echo "Packaging isis_world.p3d"
	pdeploy -n isis_world -N "IsisWorld v$(SIM_VERSION)"  -l "GPL v3" -P osx_i386 -L COPYING -t width=800 -t height=600  -v $(SIM_VERSION)  -s isis_world.p3d installer 

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


