define yum_centos_repo
[centos]
name=CentOS-$(CENTOS_RELEASE) - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=os
baseurl=http://mirrors.msk.mirantis.net/centos/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
gpgcheck=0
enabled=0
priority=10
endef

define INSTALL_CENTOS_REPO
cat > $(SANDBOX)/etc/yum.repos.d/centos.repo <<EOF
$(yum_centos_repo)
EOF
endef

# Usage:
# (eval (call prepare_openstack_source,package_name,file_name,source_path))
define prepare_openstack_source
$(BUILD_DIR)/openstack/rpm/$1.done: $(BUILD_DIR)/openstack/rpm/sources/$1/$2
$(BUILD_DIR)/openstack/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/openstack/rpm/sources/$1
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/openstack/rpm/sources/$1 && python setup.py --version sdist > $(BUILD_DIR)/openstack/rpm/$1-version-tag
endef

# Usage:
# (eval (call build_openstack_rpm,package_name))
define build_openstack_rpm
$(BUILD_DIR)/openstack/rpm/repo.done: $(BUILD_DIR)/openstack/rpm/$1.done
$(BUILD_DIR)/openstack/rpm/repo.done: $(BUILD_DIR)/openstack/rpm/$1-repocleanup.done

# You can use package name as a target, for example: make neutron
# It will build neutron rpm package
$1: $(BUILD_DIR)/openstack/rpm/$1.done

$(BUILD_DIR)/openstack/rpm/$1.done: $(BUILD_DIR)/mirror/build.done

$(BUILD_DIR)/openstack/rpm/$1.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/openstack/rpm/$1.done: export SANDBOX_UP:=$$(SANDBOX_UP)
$(BUILD_DIR)/openstack/rpm/$1.done: export SANDBOX_DOWN:=$$(SANDBOX_DOWN)
$(BUILD_DIR)/openstack/rpm/$1.done: export INSTALL_CENTOS_REPO:=$$(INSTALL_CENTOS_REPO)
$(BUILD_DIR)/openstack/rpm/$1.done: \
	$(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/openstack/rpm/RPMS/x86_64 $(BUILD_DIR)/openstack/rpm/sources/specs
	sudo sh -c "$$$${SANDBOX_UP}"
	sudo yum -c $$(SANDBOX)/etc/yum.conf --installroot=$$(SANDBOX) -y --nogpgcheck install ruby rpm-build tar python-setuptools yum-utils
	sudo mkdir -p $$(SANDBOX)/tmp/SPECS $$(SANDBOX)/tmp/SOURCES $$(SANDBOX)/tmp/BUILD $$(SANDBOX)/tmp/BUILDROOT $$(SANDBOX)/tmp/RPMS $$(SANDBOX)/tmp/SRPMS
	sudo cp $(BUILD_DIR)/openstack/rpm/sources/$1/*.tar.gz $$(SANDBOX)/tmp/SOURCES/
	sudo cp -r $(BUILD_DIR)/repos/$1-build/rpm/SOURCES/* $$(SANDBOX)/tmp/SOURCES
	sed "s/Version:.*/Version:\t`cat $(BUILD_DIR)/openstack/rpm/$1-version-tag`/" $(BUILD_DIR)/repos/$1-build/rpm/SPECS/openstack-$1.spec > $(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec
	sed -i "s/Source0:.*/Source0:\t$1-`cat $(BUILD_DIR)/openstack/rpm/$1-version-tag`\.tar\.gz/" $(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec
	sudo cp $(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec $$(SANDBOX)/tmp/
	sudo chroot $$(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -bs /tmp/openstack-$1.spec
	sudo sh -c "$$$${INSTALL_CENTOS_REPO}"
	sudo yum-builddep -c $$(SANDBOX)/etc/yum.conf --enablerepo=centos --installroot=$$(SANDBOX) -y --nogpgcheck $$(SANDBOX)/tmp/SRPMS/openstack-$1*.rpm
	sudo rm -rf $$(SANDBOX)/tmp/RPMS
	sudo chroot $$(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -ba /tmp/openstack-$1.spec
	cp $$(SANDBOX)/tmp/RPMS/*/*$1*.rpm $(BUILD_DIR)/openstack/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/build.done
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*$1-[^-]+-[^-]+.*' -delete
	$$(ACTION.TOUCH)
endef

# Hard-coded repos variables - need to replace them with proper parsing of BUILD_OPENSTACK_PACKAGES parameter
$(eval $(call build_repo,neutron,$(NEUTRON_REPO),$(NEUTRON_COMMIT),$(NEUTRON_GERRIT_URL),$(NEUTRON_GERRIT_COMMIT)))
$(eval $(call build_repo,neutron-build,$(NEUTRON_SPEC_REPO),$(NEUTRON_SPEC_COMMIT),$(NEUTRON_SPEC_GERRIT_URL),$(NEUTRON_SPEC_GERRIT_COMMIT)))
$(eval $(call prepare_openstack_source,neutron,neutron-2014.1.tar.gz,$(BUILD_DIR)/repos/neutron))

$(eval $(call build_repo,keystone,$(KEYSTONE_REPO),$(KEYSTONE_COMMIT),$(KEYSTONE_GERRIT_URL),$(KEYSTONE_GERRIT_COMMIT)))
$(eval $(call build_repo,keystone-build,$(KEYSTONE_SPEC_REPO),$(KEYSTONE_SPEC_COMMIT),$(KEYSTONE_SPEC_GERRIT_URL),$(KEYSTONE_SPEC_GERRIT_COMMIT)))
$(eval $(call prepare_openstack_source,keystone,keystone-2014.1.tar.gz,$(BUILD_DIR)/repos/keystone))

comma:=,
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_openstack_rpm,$(pkg))))

$(BUILD_DIR)/openstack/rpm/repo.done:
	find $(BUILD_DIR)/openstack/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/rpm/build.done: $(BUILD_DIR)/openstack/rpm/repo.done
	$(ACTION.TOUCH)
