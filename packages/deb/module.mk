.PHONY: clean clean-deb

clean: clean-deb

clean-deb:
	-mount | grep '$(BUILD_DIR)/packages/deb' | while read entry; do \
		set -- $$entry; \
		mntpt="$$3"; \
		sudo umount $$mntpt; \
	done
	sudo rm -rf $(BUILD_DIR)/packages/deb

$(BUILD_DIR)/packages/deb/buildd.tar.gz: SANDBOX_DEB_PKGS:=wget bzip2 apt-utils build-essential python-setuptools devscripts debhelper fakeroot
$(BUILD_DIR)/packages/deb/buildd.tar.gz: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/chroot
$(BUILD_DIR)/packages/deb/buildd.tar.gz: export SANDBOX_UBUNTU_UP:=$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/packages/deb/buildd.tar.gz: export SANDBOX_UBUNTU_DOWN:=$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/packages/deb/buildd.tar.gz: $(BUILD_DIR)/mirror/ubuntu/build.done
	sh -c "$${SANDBOX_UBUNTU_UP}"
	sh -c "$${SANDBOX_UBUNTU_DOWN}"
	sudo rm -f $(SANDBOX_UBUNTU)/var/cache/apt/archives/*.deb
	sudo tar czf $@.tmp -C $(SANDBOX_UBUNTU) .
	mv $@.tmp $@

# Usage:
# (eval (call build_deb,package_name))
define build_deb
$1-deb: $(BUILD_DIR)/packages/deb/$1.done

$(BUILD_DIR)/packages/deb/repo.done: $(BUILD_DIR)/packages/deb/$1.done
$(BUILD_DIR)/packages/deb/repo.done: $(BUILD_DIR)/packages/deb/$1-repocleanup.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/mirror/ubuntu/build.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/packages/source_$1.done
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/packages/deb/buildd.tar.gz
$(BUILD_DIR)/packages/deb/$1.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/SANDBOX/$1
$(BUILD_DIR)/packages/deb/$1.done: SANDBOX_DEB_PKGS:=apt wget bzip2 apt-utils build-essential python-setuptools devscripts debhelper fakeroot
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_UP:=$$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_DOWN:=$$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/packages/deb/packages $(BUILD_DIR)/packages/deb/sources
	if [ ! -e "$$(SANDBOX_UBUNTU)/etc/debian_version" ]; then \
		sudo tar xaf $(BUILD_DIR)/packages/deb/buildd.tar.gz -C $$(SANDBOX_UBUNTU); \
	fi
	mkdir -p $$(SANDBOX_UBUNTU)/tmp/$1/
	sudo tar zxf $(BUILD_DIR)/packages/sources/$1/$1-$(PACKAGE_VERSION).tar.gz -C $$(SANDBOX_UBUNTU)/tmp/$1/
	sudo cp -r $(SOURCE_DIR)/packages/deb/specs/$1/* $$(SANDBOX_UBUNTU)/tmp/$1/
	dpkg-checkbuilddeps $(SOURCE_DIR)/packages/deb/specs/$1/debian/control 2>&1 | sed 's/^dpkg-checkbuilddeps: Unmet build dependencies: //g' | sed 's/([^()]*)//g;s/|//g' | sudo tee $$(SANDBOX_UBUNTU)/tmp/$1.installdeps
	sudo chroot $$(SANDBOX_UBUNTU) /bin/sh -c "cat /tmp/$1.installdeps | xargs apt-get -y install"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/sh -c "cd /tmp/$1 ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
	cp $$(SANDBOX_UBUNTU)/tmp/*.deb $(BUILD_DIR)/packages/deb/packages
	sudo sh -c "$$$${SANDBOX_UBUNTU_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/deb/$1-repocleanup.done: $(BUILD_DIR)/mirror/ubuntu/build.done
	sudo find $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main -regex '.*$1_[^-]+-[^-]+.*' -delete
	$$(ACTION.TOUCH)
endef


fuel_debian_packages:=nailgun astute

$(eval $(foreach pkg,$(fuel_debian_packages),$(call build_deb,$(pkg))$(NEWLINE)))

$(BUILD_DIR)/packages/deb/repo.done:
	sudo find $(BUILD_DIR)/packages/deb/packages -name '*.deb' -exec cp -u {} $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main \;
	echo "Applying fix for upstream bug in dpkg..."
	-sudo patch -N /usr/bin/dpkg-scanpackages < $(SOURCE_DIR)/packages/dpkg.patch
	sudo $(SOURCE_DIR)/regenerate_ubuntu_repo.sh $(LOCAL_MIRROR_UBUNTU_OS_BASEURL) $(UBUNTU_RELEASE)
	$(ACTION.TOUCH)

ifneq (0,$(strip $(BUILD_DEB_PACKAGES)))
$(BUILD_DIR)/packages/deb/build.done: $(BUILD_DIR)/packages/deb/repo.done
endif

