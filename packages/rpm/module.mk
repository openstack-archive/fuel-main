/:=$(BUILD_DIR)/rpm/

$/%: /:=$/

SRC_DIR:=$/SOURCES/

$/prep.done: $(LOCAL_MIRROR)/src.done
	@mkdir -p $/SOURCES
	cp -f $(LOCAL_MIRROR)/src/* $/SOURCES/
	cp -f bin/agent bin/nailgun-agent.cron $/SOURCES/
	mkdir -p $/SOURCES/nailgun-mcagents
	cp -f mcagent/* $/SOURCES/nailgun-mcagents
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

$(BUILD_DIR)/rpm/rpm.done: $/rpm-cirros.done \
		$/rpm-rabbitmq-plugins.done \
		$/rpm-nailgun-agent.done \
		$/rpm-nailgun-mcagents.done
	$(ACTION.TOUCH)
