.PHONY: clean clean-deb

clean: clean-deb

clean-deb:
	-mount | grep '$(BUILD_DIR)/packages/deb' | while read entry; do \
		set -- $$entry; \
		mntpt="$$3"; \
		sudo umount $$mntpt; \
	done
	sudo rm -rf $(BUILD_DIR)/packages/deb

$(BUILD_DIR)/packages/deb/buildd.tar.gz: SANDBOX_DEB_PKGS:=wget bzip2 apt-utils build-essential fakeroot devscripts equivs debhelper python-setuptools python-pbr
$(BUILD_DIR)/packages/deb/buildd.tar.gz: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/chroot
$(BUILD_DIR)/packages/deb/buildd.tar.gz: export SANDBOX_UBUNTU_UP:=$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/packages/deb/buildd.tar.gz: export SANDBOX_UBUNTU_DOWN:=$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/packages/deb/buildd.tar.gz: $(BUILD_DIR)/mirror/ubuntu/reprepro.done
	sh -c "$${SANDBOX_UBUNTU_UP}"
	sh -c "$${SANDBOX_UBUNTU_DOWN}"
	sudo rm -f $(SANDBOX_UBUNTU)/var/cache/apt/archives/*.deb
	sudo tar czf $@.tmp -C $(SANDBOX_UBUNTU) .
	mv $@.tmp $@

# Usage:
# (eval (call build_deb,package_name))
define build_deb
$1-deb: $(BUILD_DIR)/packages/deb/$1.done
$(BUILD_DIR)/packages/deb/build.done: $(BUILD_DIR)/packages/deb/$1.done

$(BUILD_DIR)/mirror/ubuntu/repo.done: $(BUILD_DIR)/packages/deb/$1.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/mirror/ubuntu/reprepro.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/packages/source_$1.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/packages/deb/buildd.tar.gz
$(BUILD_DIR)/packages/deb/$1.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/SANDBOX/$1
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_UP:=$$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_DOWN:=$$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/packages/deb/packages $(BUILD_DIR)/packages/deb/sources
	mkdir -p $$(SANDBOX_UBUNTU)/tmp/$1/
	if [ ! -e "$$(SANDBOX_UBUNTU)/etc/debian_version" ]; then \
		sudo tar xaf $(BUILD_DIR)/packages/deb/buildd.tar.gz -C $$(SANDBOX_UBUNTU); \
	fi
	sudo tar zxf $(BUILD_DIR)/packages/sources/$1/$1-$(PACKAGE_VERSION).tar.gz -C $$(SANDBOX_UBUNTU)/tmp/$1/

	DEBFULLNAME=`awk -F'=' '/DEBFULLNAME/ {print $$$$2}' $(BUILD_DIR)/packages/sources/$1/version` \
		DEBEMAIL=`awk -F'=' '/DEBEMAIL/ {print $$$$2}' $(BUILD_DIR)/packages/sources/$1/version` \
		sudo -E dch -c $$(SANDBOX_UBUNTU)/tmp/$1/debian/changelog -D $(UBUNTU_RELEASE) -b --force-distribution \
		-v $(PACKAGE_VERSION)-`awk -F'=' '/DEBRELEASE/ {print $$$$2}' $(BUILD_DIR)/packages/sources/$1/version` \
		"`awk -F'=' '/DEBMSG/ {print $$$$2}' $(BUILD_DIR)/packages/sources/$1/version`"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/sh -c "mk-build-deps --install --remove --tool 'apt-get --yes --no-remove --no-install-recommends' /tmp/$1/debian/control"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/sh -c "cd /tmp/$1 ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
	cp $$(SANDBOX_UBUNTU)/tmp/*.deb $(BUILD_DIR)/packages/deb/packages
	sudo sh -c "$$$${SANDBOX_UBUNTU_DOWN}"
	$$(ACTION.TOUCH)
endef

define remove_deb
#FIXME(aglarendil): do not touch upstream repo. instead - build new repo
mkdir -p $(BUILD_DIR)/packages/deb
perl $(SOURCE_DIR)/packages/deb/genpkgnames.pl $(BUILD_DIR)/repos/$1/debian/control > $(BUILD_DIR)/packages/deb/$1.cleanup.list
cd $(LOCAL_MIRROR_UBUNTU) && cat $(BUILD_DIR)/packages/deb/$1.cleanup.list | \
xargs -n1 -I{} reprepro --confdir=$(REPREPRO_CONF_DIR) remove $(PRODUCT_NAME)$(PRODUCT_VERSION) {} $(NEWLINE)
endef

$(BUILD_DIR)/mirror/ubuntu/repo.done: $(BUILD_DIR)/packages/deb/repocleanup.done
$(BUILD_DIR)/packages/deb/repocleanup.done: $(BUILD_DIR)/mirror/ubuntu/reprepro.done
$(BUILD_DIR)/packages/deb/repocleanup.done: $(packages_list:%=$(BUILD_DIR)/packages/source_%.done)
	$(foreach pkg,$(fuel_debian_packages),$(call remove_deb,$(pkg)))
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/deb/build.done:
	$(ACTION.TOUCH)

fuel_debian_packages:=fuel-nailgun \
astute \
fuel-agent \
fuel-library$(FUEL_LIBRARY_VERSION) \
nailgun-agent \
network-checker

$(eval $(foreach pkg,$(fuel_debian_packages),$(call build_deb,$(pkg))$(NEWLINE)))
