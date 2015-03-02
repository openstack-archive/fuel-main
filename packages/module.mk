# Usage:
# (eval (call prepare_file_source,package_name,file_name,source_path,optional_prerequisite))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_file_source
ifeq ($4,)
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
else
$(BUILD_DIR)/packages/sources/$1/$2: $4
endif
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cp $3 $(BUILD_DIR)/packages/sources/$1/$2
endef

# Usage:
# (eval (call prepare_python_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_python_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/packages/sources/$1
endef

# Usage:
# (eval (call prepare_tgz_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_tgz_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && tar zcf $(BUILD_DIR)/packages/sources/$1/$2 *
endef

# Usage:
# (eval (call prepare_ruby21_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_ruby21_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && gem build *.gemspec && cp $2 $(BUILD_DIR)/packages/sources/$1/$2
endef

define prepare_git_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2:
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && git archive --format tar --worktree-attributes $4 > $(BUILD_DIR)/packages/sources/$1/$1.tar\
		&& git rev-parse $4 > $(BUILD_DIR)/packages/sources/$1/version.txt
	cd $(BUILD_DIR)/packages/sources/$1 && tar -rf $1.tar version.txt
	cd $(BUILD_DIR)/packages/sources/$1 && gzip -9 $1.tar && mv $1.tar.gz $2
endef

$(BUILD_DIR)/packages/source_%.done:
	$(ACTION.TOUCH)

#NAILGUN_PKGS
$(eval $(call prepare_git_source,nailgun,nailgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun,HEAD))
#FUEL_OSTF_PKGS
$(eval $(call prepare_git_source,fuel-ostf,fuel-ostf-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-ostf,HEAD))
#ASTUTE_PKGS
$(eval $(call prepare_git_source,astute,astute-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/astute,HEAD))
#FUELLIB_PKGS
$(eval $(call prepare_git_source,fuel-library6.1,fuel-library6.1-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-library6.1,HEAD))
#FUEL_PYTHON_PKGS
$(eval $(call prepare_git_source,python-fuelclient,python-fuelclient-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/python-fuelclient,HEAD))
#FUEL-IMAGE PKGS
$(eval $(call prepare_git_source,fuel-main,fuel-main-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-main,HEAD))

include $(SOURCE_DIR)/packages/rpm/module.mk
include $(SOURCE_DIR)/packages/deb/module.mk

.PHONY: packages packages-deb packages-rpm

ifneq ($(BUILD_PACKAGES),0)
$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/packages/deb/build.done
endif

$(BUILD_DIR)/packages/build.done:
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done
packages-rpm: $(BUILD_DIR)/packages/rpm/build.done
packages-deb: $(BUILD_DIR)/packages/deb/build.done

#FIXME(aglarendil): make sources generation uniform
#$(BUILD_DIR)/packages/source_fuel-library.done: $(BUILD_DIR)/packages/source_fuel-library6.1.done
#	ln -s $(BUILD_DIR)/packages/sources/fuel-library6.1 $(BUILD_DIR)/packages/sources/fuel-library  
#	$(ACTION.TOUCH)

###################################
#### LATE PACKAGES ################
###################################

# fuel-bootstrap-image sources
$(eval $(call prepare_file_source,fuel-bootstrap-image,linux,$(BUILD_DIR)/bootstrap/linux,$(BUILD_DIR)/bootstrap/linux))
$(eval $(call prepare_file_source,fuel-bootstrap-image,initramfs.img,$(BUILD_DIR)/bootstrap/initramfs.img,$(BUILD_DIR)/bootstrap/initramfs.img))
$(eval $(call prepare_file_source,fuel-bootstrap-image,bootstrap.rsa,$(SOURCE_DIR)/bootstrap/ssh/id_rsa,$(SOURCE_DIR)/bootstrap/ssh/id_rsa))

# fuel-target-centos-images sources
$(eval $(call prepare_file_source,fuel-target-centos-images,fuel-target-centos-images.tar,$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME),$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME)))

.PHONY: packages-late packages-rpm-late

ifneq ($(BUILD_PACKAGES),0)
$(BUILD_DIR)/packages/build-late.done: \
		$(BUILD_DIR)/packages/rpm/build-late.done
endif

$(BUILD_DIR)/packages/build-late.done:
	$(ACTION.TOUCH)

packages-late: $(BUILD_DIR)/packages/build-late.done
packages-rpm-late: $(BUILD_DIR)/packages/rpm/build-late.done

.PHONY: sources

sources: $(packages_list:%=$(BUILD_DIR)/packages/source_%.done)
