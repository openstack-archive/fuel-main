.PHONY: clean clean-deb

include $(SOURCE_DIR)/packages/deb/debian-boot/module.mk

clean: clean-deb

clean-deb:
	-sudo umount $(BUILD_DIR)/packages/deb/SANDBOX/proc
	-sudo umount $(BUILD_DIR)/packages/deb/SANDBOX/dev
	sudo rm -rf $(BUILD_DIR)/packages/deb

# Usage:
# (eval (call build_deb,package_name))
define build_deb
$(BUILD_DIR)/packages/deb/repo.done: $(BUILD_DIR)/packages/deb/$1.done
$(BUILD_DIR)/packages/deb/repo.done: $(BUILD_DIR)/packages/deb/$1-repocleanup.done

$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/mirror/ubuntu/build.done

$(BUILD_DIR)/packages/deb/$1.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/SANDBOX
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_UP:=$$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/packages/deb/$1.done: export SANDBOX_UBUNTU_DOWN:=$$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/packages/deb/$1.done: $(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/packages/deb/packages $(BUILD_DIR)/packages/deb/sources
	mkdir -p $$(SANDBOX_UBUNTU)
	mkdir -p $$(SANDBOX_UBUNTU)/proc
	sed -e "s/@@UBUNTU_RELEASE@@/$(UBUNTU_RELEASE)/g" $$(SOURCE_DIR)/packages/multistrap.conf | sudo tee $$(SANDBOX_UBUNTU)/multistrap.conf
	sudo sh -c "$$$${SANDBOX_UBUNTU_UP}"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "apt-get update"
	sudo mkdir -p $$(SANDBOX_UBUNTU)/tmp/$1
ifeq ($1,$(filter $1,nailgun-net-check python-tasklib))
	tar zxf $(BUILD_DIR)/packages/sources/$1/$(subst python-,,$1)*.tar.gz -C $(BUILD_DIR)/packages/deb/sources
	sudo cp -r $(BUILD_DIR)/packages/deb/sources/$(subst python-,,$1)*/* $$(SANDBOX_UBUNTU)/tmp/$1/
endif
	sudo cp -r $(BUILD_DIR)/packages/sources/$1/* $$(SANDBOX_UBUNTU)/tmp/$1/
	sudo cp -r $(SOURCE_DIR)/packages/deb/specs/$1/* $$(SANDBOX_UBUNTU)/tmp/$1/
	dpkg-checkbuilddeps $(SOURCE_DIR)/packages/deb/specs/$1/debian/control 2>&1 | sed 's/^dpkg-checkbuilddeps: Unmet build dependencies: //g' | sed 's/([^()]*)//g;s/|//g' | sudo tee $$(SANDBOX_UBUNTU)/tmp/$1.installdeps
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "cat /tmp/$1.installdeps | xargs apt-get -y install"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "cd /tmp/$1 ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
	cp $$(SANDBOX_UBUNTU)/tmp/*$1*.deb $(BUILD_DIR)/packages/deb/packages
	sudo rm -rf $$(SANDBOX_UBUNTU)/tmp/*
	sudo sh -c "$$$${SANDBOX_UBUNTU_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/deb/$1-repocleanup.done: $(BUILD_DIR)/mirror/ubuntu/build.done
	sudo find $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main -regex '.*$1_[^-]+-[^-]+.*' -delete
	$$(ACTION.TOUCH)
endef

$(eval $(call build_deb,fencing-agent))
$(eval $(call build_deb,nailgun-mcagents))
$(eval $(call build_deb,nailgun-net-check))
$(eval $(call build_deb,nailgun-agent))
$(eval $(call build_deb,python-tasklib))

$(BUILD_DIR)/packages/deb/repo.done:
	sudo find $(BUILD_DIR)/packages/deb/packages -name '*.deb' -exec cp -u {} $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main \;
	echo "Applying fix for upstream bug in dpkg..."
	-sudo patch -N /usr/bin/dpkg-scanpackages < $(SOURCE_DIR)/packages/dpkg.patch
	sudo $(SOURCE_DIR)/regenerate_ubuntu_repo.sh $(LOCAL_MIRROR_UBUNTU_OS_BASEURL) $(UBUNTU_RELEASE)
	$(ACTION.TOUCH)

ifneq (0,$(strip $(BUILD_DEB_PACKAGES)))
$(BUILD_DIR)/packages/deb/build.done: $(BUILD_DIR)/packages/deb/repo.done
endif

$(BUILD_DIR)/packages/deb/build.done: $(BUILD_DIR)/packages/deb/debian-boot/build.done
	$(ACTION.TOUCH)
