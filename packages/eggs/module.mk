include $(SOURCE_DIR)/nailgun/module.mk

.PHONY: nailgun nailgun_version

$(BUILD_DIR)/packages/eggs/build.done: \
		$(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
	mkdir -p $(LOCAL_MIRROR_EGGS)
	find $(BUILD_DIR)/packages/eggs/ -maxdepth 1 -type f ! -name "build.done" \
	    -exec cp {} $(LOCAL_MIRROR_EGGS) \;
	$(ACTION.TOUCH)

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

$(eval $(call build_egg,fuel-ostf-tests,$(OSTF_TESTS_SHA),ostf_tests,$(OSTF_TESTS_VER)))
$(eval $(call build_egg,fuel-ostf-plugin,$(OSTF_PLUGIN_SHA),testing_adapter,$(OSTF_PLUGIN_VER)))
$(eval $(call build_egg,GateOne,bb003114b4e84e9425fd02fd1ee615d4dd2113e7,gateone,1.2.0))

nailgun: $(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
nailgun_version:
	@echo $(NAILGUN_VERSION)
