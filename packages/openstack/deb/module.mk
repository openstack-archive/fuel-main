# Usage:
# (eval (call build_openstack_deb,package_name))
define build_openstack_deb
$(BUILD_DIR)/openstack/deb/repo.done: $(BUILD_DIR)/openstack/deb/$1.done
$(BUILD_DIR)/openstack/deb/repo.done: $(BUILD_DIR)/openstack/deb/$1-repocleanup.done

$(BUILD_DIR)/openstack/deb/$1.done: $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/openstack/deb/$1.done: $(BUILD_DIR)/openstack/source_$1.done

$(BUILD_DIR)/openstack/deb/$1.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/packages/deb/SANDBOX
$(BUILD_DIR)/openstack/deb/$1.done: SANDBOX_DEB_PKGS:=apt wget bzip2 apt-utils build-essential python-setuptools devscripts debhelper fakeroot 
$(BUILD_DIR)/openstack/deb/$1.done: export SANDBOX_UBUNTU_UP:=$$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/openstack/deb/$1.done: export SANDBOX_UBUNTU_DOWN:=$$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/openstack/deb/$1.done: $(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/openstack/deb/packages $(BUILD_DIR)/openstack/deb/deps
#	create sandbox if does not exist
	test -e $$(SANDBOX_UBUNTU)/etc/debian_version || sudo sh -c "$$$${SANDBOX_UBUNTU_UP}"
#	mount proc if not mounted
	mountpoint -q $$(SANDBOX_UBUNTU)/proc || sudo mount -t proc sandbox_ubuntu_proc $$(SANDBOX_UBUNTU)/proc
	echo deb mirror://mirrors.ubuntu.com/mirrors.txt $(UBUNTU_RELEASE) main universe multiverse | sudo tee $$(SANDBOX_UBUNTU)/etc/apt/sources.list.d/main.list
	echo deb mirror://mirrors.ubuntu.com/mirrors.txt $(UBUNTU_RELEASE)-updates main universe multiverse | sudo tee $$(SANDBOX_UBUNTU)/etc/apt/sources.list.d/updates.list
	echo deb mirror://mirrors.ubuntu.com/mirrors.txt $(UBUNTU_RELEASE)-security main universe multiverse | sudo tee $$(SANDBOX_UBUNTU)/etc/apt/sources.list.d/security.list
	echo deb http://mirror.fuel-infra.org/repos/ubuntu-fuel-master/ubuntu/ / | sudo tee $$(SANDBOX_UBUNTU)/etc/apt/sources.list.d/master.list
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "apt-get update"
	sudo tar zxf $(BUILD_DIR)/openstack/sources/$1/$1*.tar.gz -C $$(SANDBOX_UBUNTU)/tmp/
	sudo cp -r $(BUILD_DIR)/repos/$1-build/debian $$(SANDBOX_UBUNTU)/tmp/$1-*/
	dpkg-checkbuilddeps $(BUILD_DIR)/repos/$1-build/debian/control 2>&1 | sed 's/^dpkg-checkbuilddeps: Unmet build dependencies: //g' | sed 's/([^()]*)//g;s/|//g' | sudo tee $$(SANDBOX_UBUNTU)/tmp/$1.installdeps
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "cat /tmp/$1.installdeps | xargs apt-get -y install"
	sudo chroot $$(SANDBOX_UBUNTU) /bin/bash -c "cd /tmp/$1-* ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
	cp $$(SANDBOX_UBUNTU)/tmp/*$1*.deb $(BUILD_DIR)/openstack/deb/packages
	sudo rm -rf $$(SANDBOX_UBUNTU)/tmp/*$1*
	grep ^Package: $(BUILD_DIR)/repos/$1-build/debian/control | cut -d" " -f2 | sudo tee $(BUILD_DIR)/packages/deb/$1.pkg.list
	sudo sh -c "$$$${SANDBOX_UBUNTU_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/deb/$1-repocleanup.done: $(BUILD_DIR)/mirror/build.done
	for pkg in `cat $(BUILD_DIR)/packages/deb/$1.pkg.list`; do EXPR=".*"$$$$pkg"_[^-]+-[^-]+.*" ; sudo find $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main -regex $$$$EXPR -delete ; done
	$$(ACTION.TOUCH)
endef

ifneq ($(strip $(BUILD_OPENSTACK_PACKAGES)),)
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call set_vars,$(pkg))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_openstack_deb,$(pkg))))
endif

$(BUILD_DIR)/openstack/deb/repo.done:
	sudo cp -a $(BUILD_DIR)/packages/deb/*.pkg.list $(SOURCE_DIR)/packages/openstack/deb/get_deps.sh $(BUILD_DIR)/packages/deb/SANDBOX/
	sudo chroot $(BUILD_DIR)/packages/deb/SANDBOX /bin/bash -c "/get_deps.sh"
	sudo mv $(BUILD_DIR)/packages/deb/SANDBOX/repo/download/*.deb $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main/
	sudo find $(BUILD_DIR)/openstack/deb/packages -name '*.deb' -exec cp -u {} $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main \;
	sudo $(SOURCE_DIR)/regenerate_ubuntu_repo.sh $(LOCAL_MIRROR_UBUNTU_OS_BASEURL) $(UBUNTU_RELEASE)
	$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/deb/build.done: $(BUILD_DIR)/openstack/deb/repo.done
	$(ACTION.TOUCH)
