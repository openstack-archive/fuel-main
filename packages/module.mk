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

# Prepare sources + version file in format:
#
# VERSION=$(PRODUCT_VERSION)
# if gerrit commit is given then
#   RELEASE=${commit_num}.0.gerrit${request_number}.${patchset_number}.git${git_sha}
# else
#   RELEASE=${commit_num}.1.git${git_sha}
# DEBFULLNAME=Commit Author
# DEBEMAIL=Commit Author email address
# DEBMSG=Commit message
define prepare_git_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: VERSIONFILE:=$(BUILD_DIR)/packages/sources/$1/version
$(BUILD_DIR)/packages/sources/$1/$2:
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && git archive --format tar --worktree-attributes $4 > $(BUILD_DIR)/packages/sources/$1/$1.tar
	echo VERSION=$(PACKAGE_VERSION) > $$(VERSIONFILE)
	test -z $(GERRIT_BRANCH) && echo -n RELEASE=`git -C $3 rev-list --no-merges $4 --count` >> $$(VERSIONFILE) \
		|| echo -n RELEASE=`git -C $3 rev-list --no-merges $(GERRIT_BRANCH) --count` >> $$(VERSIONFILE)
	test -z $(GERRIT_BRANCH) && echo -n ".1" >> $$(VERSIONFILE) \
		|| echo -n ".2.gerrit"`echo $5 | sed 's].*\/.*\/\(.*\/.*\)]\1]' | sed 's/\//./'` >> $$(VERSIONFILE)
	test -z $(GERRIT_BRANCH) && echo ".git`git -C $3 rev-parse --short $4`" >> $$(VERSIONFILE) \
		|| echo ".git`git -C $3 rev-parse --short $(GERRIT_BRANCH)`" >> $$(VERSIONFILE)
	echo DEBFULLNAME=`git -C $3 log -1 --pretty=format:%an` >> $$(VERSIONFILE)
	echo DEBEMAIL=`git -C $3 log -1 --pretty=format:%ae` >> $$(VERSIONFILE)
	echo DEBMSG=`git -C $3 log -1 --pretty=%s` >> $$(VERSIONFILE)
	cd $(BUILD_DIR)/packages/sources/$1 && tar -rf $1.tar version
	cd $(BUILD_DIR)/packages/sources/$1 && gzip -9 $1.tar && mv $1.tar.gz $2
endef

$(BUILD_DIR)/packages/source_%.done:
	$(ACTION.TOUCH)

#NAILGUN_PKGS
$(eval $(call prepare_git_source,nailgun,nailgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun,HEAD,$(NAILGUN_GERRIT_COMMIT)))
#FUEL_OSTF_PKGS
$(eval $(call prepare_git_source,fuel-ostf,fuel-ostf-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-ostf,HEAD,$(OSTF_GERRIT_COMMIT)))
#ASTUTE_PKGS
$(eval $(call prepare_git_source,astute,astute-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/astute,HEAD,$(ASTUTE_GERRIT_COMMIT)))
#FUELLIB_PKGS
$(eval $(call prepare_git_source,fuel-library$(PRODUCT_VERSION),fuel-library$(PRODUCT_VERSION)-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-library$(PRODUCT_VERSION),HEAD,$(FUELLIB_GERRIT_COMMIT)))
#FUEL_PYTHON_PKGS
$(eval $(call prepare_git_source,python-fuelclient,python-fuelclient-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/python-fuelclient,HEAD,$(PYTHON_FUELCLIENT_GERRIT_COMMIT)))
#FUEL-IMAGE PKGS
$(eval $(call prepare_git_source,fuel-main,fuel-main-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-main,HEAD,$(FUELMAIN_GERRIT_COMMIT)))

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
#$(BUILD_DIR)/packages/source_fuel-library.done: $(BUILD_DIR)/packages/source_fuel-library$(PRODUCT_VERSION).done
#	ln -s $(BUILD_DIR)/packages/sources/fuel-library$(PRODUCT_VERSION) $(BUILD_DIR)/packages/sources/fuel-library  
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

$(BUILD_DIR)/packages/build-late.done: \
		$(BUILD_DIR)/packages/rpm/build-late.done \
		$(BUILD_DIR)/packages/rpm/fuel-docker-images.done
	$(ACTION.TOUCH)

packages-late: $(BUILD_DIR)/packages/build-late.done
packages-rpm-late: $(BUILD_DIR)/packages/rpm/build-late.done

.PHONY: sources

sources: $(packages_list:%=$(BUILD_DIR)/packages/source_%.done)
