/:=$(BUILD_DIR)/rpm/

$/%: /:=$/

SANDBOX:=$/SANDBOX/
CHROOT_BOX:=sudo chroot $(SANDBOX)
SRC_DIR:=$/SOURCES/
SAND_YUM:=sudo yum --installroot=`readlink -f $(SANDBOX)` -y --nogpgcheck
SAND_RPM:=sudo rpm --root=`readlink -f $(SANDBOX)`
SAND_REQ:=rpm-build tar gcc flex make byacc python-devel.x86_64 glibc-devel \
	  glibc-headers kernel-headers

.PHONY: clean clean_rpm

clean: clean_rpm

clean_rpm:
	sudo rm -rf $(BUILD_DIR)/rpm

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f -m $(RPM_DIR))/Packages
gpgcheck=0
enabled=1
endef

$(SANDBOX)/etc/yum.repos.d/mirror.repo: export contents:=$(yum_local_repo)
$(SANDBOX)/etc/yum.repos.d/mirror.repo:
	mkdir -p $(@D) || echo "$(@D) already exists"
	sudo sh -c "echo \"$${contents}\" > $@"

$/prep.done: $(LOCAL_MIRROR)/src.done \
	     $(LOCAL_MIRROR)/repo.done \
	     $(SANDBOX)/etc/yum.repos.d/mirror.repo
	mkdir -p $(SRC_DIR)
	cp -f packages/rpm/patches/* $(SRC_DIR)
	cp -f $(LOCAL_MIRROR)/src/* $(SRC_DIR)
	cp -f bin/agent bin/nailgun-agent.cron $(SRC_DIR)
	mkdir -p $/SOURCES/nailgun-mcagents
	cp -f mcagent/* $(SRC_DIR)nailgun-mcagents
	find $(LOCAL_MIRROR) -name centos-release* | head | xargs sudo rpm -i --root=$(SANDBOX) || echo "chroot already prepared"
	sudo rm -f $(SANDBOX)/etc/yum.repos.d/Cent*
	$(SAND_RPM) --rebuilddb
	$(SAND_YUM) install $(SAND_REQ)
	$(ACTION.TOUCH)

$/rpm-cirros.done: $/prep.done packages/rpm/specs/cirros-0.3.0.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/cirros-0.3.0.spec
	$(ACTION.TOUCH)

$/rpm-rabbitmq-plugins.done: $/prep.done packages/rpm/specs/rabbitmq-plugins.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/rabbitmq-plugins.spec
	$(ACTION.TOUCH)

$/rpm-nailgun-agent.done: $/prep.done packages/rpm/specs/nailgun-agent.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/nailgun-agent.spec
	$(ACTION.TOUCH)

$/rpm-nailgun-mcagents.done: $/prep.done packages/rpm/specs/nailgun-mcagents.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/nailgun-mcagents.spec
	$(ACTION.TOUCH)

$/rpm-nailgun-net-check.done: $/prep.done packages/rpm/specs/nailgun-net-check.spec
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES
	sudo cp packages/rpm/nailgun-net-check/net_probe.py $(SANDBOX)/tmp/SOURCES
	sudo cp packages/rpm/specs/nailgun-net-check.spec $(SANDBOX)/tmp
	sudo cp packages/rpm/patches/* $(SANDBOX)/tmp/SOURCES
	sudo cp $(LOCAL_MIRROR)/src/* $(SANDBOX)/tmp/SOURCES
	$(CHROOT_BOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/nailgun-net-check.spec
	cp $(SANDBOX)/tmp/RPMS/x86_64/* $/RPMS/x86_64/
	$(ACTION.TOUCH)

$(BUILD_DIR)/rpm/rpm.done: $/rpm-cirros.done \
		$/rpm-rabbitmq-plugins.done \
		$/rpm-nailgun-agent.done \
		$/rpm-nailgun-mcagents.done \
		$/rpm-nailgun-net-check.done
	find $/RPMS -name '*.rpm' -exec cp -n {} $(CENTOS_REPO_DIR)/Packages \;
	createrepo -g `readlink -f "$(CENTOS_REPO_DIR)repodata/comps.xml"` -o $(CENTOS_REPO_DIR)Packages $(CENTOS_REPO_DIR)Packages
	$(ACTION.TOUCH)
