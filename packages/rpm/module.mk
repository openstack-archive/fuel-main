/:=$(BUILD_DIR)/packages/rpm/

$/%: /:=$/

.PHONY: rpm

rpm: $/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm

$/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm: $/SOURCES/cirros-0.3.0-x86_64-uec.tar.gz
	rpmbuild -vv --define '_topdir $(CURDIR)/$/' -ba packages/rpm/specs/cirros-0.3.0.spec

$/SOURCES/cirros-0.3.0-x86_64-uec.tar.gz:
	mkdir -p $(CURDIR)/$/SOURCES
	cd $(CURDIR)/$/SOURCES && \
	wget https://launchpad.net/cirros/trunk/0.3.0/+download/cirros-0.3.0-x86_64-uec.tar.gz

$(BUILD_DIR)/packages/rpm/rpm.done: rpm
	$(ACTION.TOUCH)
