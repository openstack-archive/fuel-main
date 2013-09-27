.PHONY: nailgun shotgun

$(BUILD_DIR)/packages/eggs/build.done: \
		$(BUILD_DIR)/packages/eggs/nailgun.done \
		$(BUILD_DIR)/packages/eggs/shotgun.done
	mkdir -p $(LOCAL_MIRROR_EGGS)
	find $(BUILD_DIR)/packages/eggs/ -maxdepth 1 -type f ! -name "build.done" \
	    -exec cp {} $(LOCAL_MIRROR_EGGS) \;
	$(ACTION.TOUCH)

# Target for building egg from checked-out repo
# Usage: build_egg <repo_name> <package_name> <version>
define build_repo_egg
$(BUILD_DIR)/packages/eggs/build.done: \
	$(BUILD_DIR)/packages/eggs/$2-$3.tar.gz

$(BUILD_DIR)/packages/eggs/$2-$3.tar.gz: $(BUILD_DIR)/repos/$1.done
	(cd $(BUILD_DIR)/repos/$1 && python setup.py sdist)
	cp $(BUILD_DIR)/repos/$1/dist/$2-$3.tar.gz $(BUILD_DIR)/packages/eggs
endef

# Target for building egg from github
# Usage: build_egg <repo_name> <SHA> <package_name> <VERSION>
define build_egg
$(BUILD_DIR)/packages/eggs/build.done: \
	$(BUILD_DIR)/packages/eggs/$3-$4.tar.gz

$(BUILD_DIR)/packages/eggs/$3-$4.tar.gz: $(LOCAL_MIRROR_SRC)/$2.zip
	mkdir -p $(BUILD_DIR)/packages/eggs
	rm -rf $(BUILD_DIR)/packages/eggs/$1-$2
	unzip -q $(LOCAL_MIRROR_SRC)/$2.zip -d $(BUILD_DIR)/packages/eggs
	(cd $(BUILD_DIR)/packages/eggs/$1-$2 && python setup.py sdist)
	cp $(BUILD_DIR)/packages/eggs/$1-$2/dist/$3-$4.tar.gz $(BUILD_DIR)/packages/eggs
endef

# OSTF eggs version are hardcoded here and in fuel/deployment/puppet/nailgun/manifests/ostf.pp
$(eval $(call build_repo_egg,ostf,fuel_ostf,0.1))
$(eval $(call build_egg,GateOne,bb003114b4e84e9425fd02fd1ee615d4dd2113e7,gateone,1.2.0))

nailgun: $(BUILD_DIR)/packages/eggs/nailgun.done
shotgun: $(BUILD_DIR)/packages/eggs/shotgun.done

$(BUILD_DIR)/packages/eggs/nailgun.done: $(call depv,NO_UI_OPTIMIZE) \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/nailgun) \
		$(BUILD_DIR)/repos/nailgun.done
ifeq ($(NO_UI_OPTIMIZE),0)
	mkdir -p $(BUILD_DIR)/packages/eggs
	cp -r $(BUILD_DIR)/repos/nailgun/nailgun $(BUILD_DIR)/packages/eggs
	cd $(BUILD_DIR)/repos/nailgun/nailgun && \
		r.js -o build.js dir=$(BUILD_DIR)/packages/eggs/nailgun/static
	rm -rf $(BUILD_DIR)/packages/eggs/nailgun/static/templates
	rm -f $(BUILD_DIR)/packages/eggs/nailgun/static/build.txt
	find $(BUILD_DIR)/packages/eggs/nailgun/static/css -type f ! -name main.css -delete
	find $(BUILD_DIR)/packages/eggs/nailgun/static/js -type f ! -name main.js -and ! -name require.js -delete
	cd $(BUILD_DIR)/packages/eggs/nailgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs
else
	cd $(BUILD_DIR)/repos/nailgun/nailgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs
endif
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/eggs/shotgun.done: \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/shotgun) \
		$(BUILD_DIR)/repos/nailgun.done
	cd $(BUILD_DIR)/repos/nailgun/shotgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs

test-unit: test-unit-nailgun

.PHONY: test-unit test-unit-nailgun
test-unit-nailgun: $(BUILD_DIR)/repos/nailgun.done
	cd $(BUILD_DIR)/repos/nailgun/nailgun && ./run_tests.sh
