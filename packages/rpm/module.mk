/:=$(BUILD_DIR)/rpm/

$/%: /:=$/

SRC_DIR:=$/SOURCES/


$/prep.done: $(LOCAL_MIRROR)/src.done
	cp -f $(LOCAL_MIRROR)/src/* $/SOURCES/
	$(ACTION.TOUCH)

$/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm: $/prep.done packages/rpm/specs/cirros-0.3.0.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/cirros-0.3.0.spec

$/RPMS/x86_64/rabbitmq-plugins-2.6.1.rpm: $/prep.done packages/rpm/specs/rabbitmq-plugins.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/rabbitmq-plugins.spec

$(BUILD_DIR)/rpm/rpm.done: $/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm \
	    $/RPMS/x86_64/rabbitmq-plugins-2.6.1.rpm
	$(ACTION.TOUCH)
