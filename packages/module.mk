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

# Prepare sources + rpm_changelog + version file in format:
#
# VERSION=$(PRODUCT_VERSION)
# RPMRELEASE=1.mos${commit_num}
# DEBRELEASE=1~u14.04+mos${commit_num}
# DEBFULLNAME=Commit Author
# DEBEMAIL=Commit Author email address
# DEBMSG={commit_sha} {Commit message}
define prepare_git_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: VERSIONFILE:=$(BUILD_DIR)/packages/sources/$1/version
$(BUILD_DIR)/packages/sources/$1/$2: GIT_VERSIONS:=$(BUILD_DIR)/listing_git_source_versions.txt
$(BUILD_DIR)/packages/sources/$1/$2: CHANGELOGFILE:=$(BUILD_DIR)/packages/sources/$1/changelog
$(BUILD_DIR)/packages/sources/$1/$2:
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && git archive --format tar --worktree-attributes $4 > $(BUILD_DIR)/packages/sources/$1/$1.tar
	echo VERSION=$(PACKAGE_VERSION) > $$(VERSIONFILE)
	echo RPMRELEASE=1.mos`git -C $3 rev-list --no-merges $4 --count` >> $$(VERSIONFILE)
	echo "%changelog\n* `LC_TIME=C date +\"%a %b %d %Y\"` `git -C $3 log -1 --pretty=format:%an` \
		<`git -C $3 log -1 --pretty=format:%ae`> - $(PACKAGE_VERSION)-1.mos`git -C $3 rev-list --no-merges $4 --count`" > $$(CHANGELOGFILE)
	echo "`git -C $3 log -10 --pretty='- %h %s'`" >> $$(CHANGELOGFILE)
	echo DEBRELEASE=1~u14.04+mos`git -C $3 rev-list --no-merges $4 --count` >> $$(VERSIONFILE)
	echo DEBFULLNAME=`git -C $3 log -1 --pretty=format:%an` >> $$(VERSIONFILE)
	echo DEBEMAIL=`git -C $3 log -1 --pretty=format:%ae` >> $$(VERSIONFILE)
	echo DEBMSG=`git -C $3 rev-parse --short HEAD` `git -C $3 log -1 --pretty=%s` >> $$(VERSIONFILE)
	echo $2=`git -C $3 rev-parse HEAD` >> $$(GIT_VERSIONS)
	cd $(BUILD_DIR)/packages/sources/$1 && tar -rf $1.tar version
ifneq ($(USE_PREDEFINED_FUEL_LIB_PUPPET_MODULES),)
	if [ "$1" = "fuel-library$(FUEL_LIBRARY_VERSION)" ]; then cd $(BUILD_DIR)/packages/sources/$1 && tar -rf $1.tar upstream_modules.tar.gz; fi
endif
	cd $(BUILD_DIR)/packages/sources/$1 && gzip -9 $1.tar && mv $1.tar.gz $2
endef

# fuel-library offline build hook
ifneq ($(USE_PREDEFINED_FUEL_LIB_PUPPET_MODULES),)
$(BUILD_DIR)/packages/sources/fuel-library$(FUEL_LIBRARY_VERSION)/upstream_modules.tar.gz:
	@mkdir -p $(@D)
	wget -nv $(USE_PREDEFINED_FUEL_LIB_PUPPET_MODULES) -O $@.tmp
	mv $@.tmp $@

$(BUILD_DIR)/packages/source_fuel-library$(FUEL_LIBRARY_VERSION).done: \
	$(BUILD_DIR)/packages/sources/fuel-library$(FUEL_LIBRARY_VERSION)/upstream_modules.tar.gz
endif

$(BUILD_DIR)/packages/source_%.done:
	$(ACTION.TOUCH)

#NAILGUN_PKGS
$(eval $(call prepare_git_source,fuel-nailgun,fuel-nailgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-nailgun,HEAD,$(NAILGUN_GERRIT_COMMIT)))
#FUEL_OSTF_PKGS
$(eval $(call prepare_git_source,fuel-ostf,fuel-ostf-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-ostf,HEAD,$(OSTF_GERRIT_COMMIT)))
#ASTUTE_PKGS
$(eval $(call prepare_git_source,astute,astute-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/astute,HEAD,$(ASTUTE_GERRIT_COMMIT)))
#FUELLIB_PKGS
$(eval $(call prepare_git_source,fuel-library$(FUEL_LIBRARY_VERSION),fuel-library$(FUEL_LIBRARY_VERSION)-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-library$(FUEL_LIBRARY_VERSION),HEAD,$(FUELLIB_GERRIT_COMMIT)))
#FUEL_PYTHON_PKGS
$(eval $(call prepare_git_source,python-fuelclient,python-fuelclient-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/python-fuelclient,HEAD,$(PYTHON_FUELCLIENT_GERRIT_COMMIT)))
#FUEL_AGENT_PKGS
$(eval $(call prepare_git_source,fuel-agent,fuel-agent-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-agent,HEAD,$(FUEL_AGENT_GERRIT_COMMIT)))
#FUEL_NAILGUN_AGENT_PKGS
$(eval $(call prepare_git_source,nailgun-agent,nailgun-agent-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun-agent,HEAD,$(FUEL_NAILGUN_AGENT_GERRIT_COMMIT)))
#FUEL-IMAGE PKGS
$(eval $(call prepare_git_source,fuel-main,fuel-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-main,HEAD,$(FUELMAIN_GERRIT_COMMIT)))
#FUEL-MIRROR PKGS
$(eval $(call prepare_git_source,fuel-mirror,fuel-mirror-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-mirror,HEAD,$(FUEL_MIRROR_GERRIT_COMMIT)))
#FUEL-MENU PKGS
$(eval $(call prepare_git_source,fuelmenu,fuelmenu-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuelmenu,HEAD,$(FUELMENU_GERRIT_COMMIT)))
#FUEL-UI PKGS
$(eval $(call prepare_git_source,fuel-ui,fuel-ui-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/fuel-ui,HEAD,$(FUEL_UI_GERRIT_COMMIT)))
#SHOTGUN PKGS
$(eval $(call prepare_git_source,shotgun,shotgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/shotgun,HEAD,$(SHOTGUN_GERRIT_COMMIT)))
#NETWORK-CHECKER PKGS
$(eval $(call prepare_git_source,network-checker,network-checker-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/network-checker,HEAD,$(NETWORKCHECKER_GERRIT_COMMIT)))

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

.PHONY: sources

sources: $(packages_list:%=$(BUILD_DIR)/packages/source_%.done)
