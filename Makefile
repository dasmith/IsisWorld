SIM_NAME=IsisWorld
SIM_VERSION=0.5

make: main.py
	ipython -c "%run main.py -D"

doc: main.py
	apydia -d docs -o -t "IsisWorld v$(SIM_VERSION)" -p markdown src

clean:
	rm -rf **/*.pyc
	rm -rf osx_i386 osx_ppc linux_amd64 linux_i386 win32
	rm packp3d.p3d.*
	rm pdeploy.p3d.*

p3d:
	wget http://runtime-dev.panda3d.org/ppackage_dev.p3d
	wget http://runtime-dev.panda3d.org/packp3d_dev.p3d
	wget http://runtime-dev.panda3d.org/pdeploy_dev.p3d

package:
	panda3d ppackage_dev.p3d -i . isisworld.pdef
	panda3d pdeploy_dev.p3d -N "IsisWorld" -n isisworld -t width=800 -t height=600 -v $(SIM_VERSION) isisworld.$(SIM_VERSION).p3d standalone

mac:
	rm -rf isisworld.$(SIM_VERSION).p3d
	panda3d ppackage_dev.p3d -i . isisworld.pdef
	panda3d pdeploy_dev.p3d -N "IsisWorld" -n isisworld -t width=800 -t height=600 -P osx_i386 v $(SIM_VERSION) isisworld.$(SIM_VERSION).p3d standalone

profile:
	echo "after running isisworld, run: runsnake stats.prof"
	python -m cProfile -o stats.prof main.py
	# then run runsnake stats.prof

deploy: package
	echo "Making cross-platform builds and uploading them"
	rm -rf scenarios/*.pyc; rm -rf scenarios/*.pyo
	rm -rf $(SIM_VERSION); mkdir $(SIM_VERSION)
	for arg in linux_amd64 linux_i386 osx_i386 osx_ppc win32; do\
		rm -rf $(SIM_NAME)_$(SIM_VERSION); mkdir $(SIM_NAME)_$(SIM_VERSION) ;\
	      	echo mv $$arg/* $(SIM_NAME)_$(SIM_VERSION) ;\
	      	mv $$arg/* $(SIM_NAME)_$(SIM_VERSION) ;\
			cp -rf DIST_README $(SIM_NAME)_$(SIM_VERSION)/README ;\
			cp -rf license.txt $(SIM_NAME)_$(SIM_VERSION)/COPYING ;\
			cp -rf scenarios $(SIM_NAME)_$(SIM_VERSION) ;\
		tar cf $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar $(SIM_NAME)_$(SIM_VERSION) ;\
		gzip $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar ;\
		mv $(SIM_NAME)_$(SIM_VERSION)_$$arg.tar.gz $(SIM_VERSION)/ ; \
		done
	rsync -a $(SIM_VERSION) dustin@ml.media.mit.edu:public_html/isisworld/

