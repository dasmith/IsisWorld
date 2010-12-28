make:
	./osx_i386/isisworld

clean:
	rm *p3d*

p3d:
	wget http://runtime-dev.panda3d.org/ppackage_dev.p3d
	wget http://runtime-dev.panda3d.org/packp3d_dev.p3d
	wget http://runtime-dev.panda3d.org/pdeploy_dev.p3d

package:
	rm -rf isisworld.0.5.p3d
	panda3d ppackage_dev.p3d -i . isisworld.pdef
	panda3d pdeploy_dev.p3d -N "IsisWorld" -n isisworld -t width=800 -t height=600 -P osx_i386 isisworld.0.5.p3d standalone

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
	rsync -a builds dustin@ml.media.mit.edu:public_html/isisworld/$(SIM_VERSION)


