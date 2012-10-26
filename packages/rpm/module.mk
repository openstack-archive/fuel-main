/:=$(BUILD_DIR)/rpm/

$/%: /:=$/

SRC_FILES:=cirros-0.3.0-x86_64-uec.tar.gz
ifeq ($(IGNORE_MIRROR),1)
define SRC_URLS
https://launchpad.net/cirros/trunk/0.3.0/+download/cirros-0.3.0-x86_64-uec.tar.gz
endef
else
SRC_URLS:=$(addprefix $(MIRROR_URL)/sources/,$(SRC_FILES))
endif

export SRC_URLS
SRC_DIR:=$/SOURCES/

$/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm: $/SOURCES/cirros-0.3.0-x86_64-uec.tar.gz packages/rpm/specs/cirros-0.3.0.spec
	rpmbuild -vv --define "_topdir `readlink -f $/`" -ba packages/rpm/specs/cirros-0.3.0.spec

$(BUILD_DIR)/rpm/rpm.done: $/RPMS/x86_64/cirros-uec-0.3.0-1.x86_64.rpm
	$(ACTION.TOUCH)

$(addprefix $(SRC_DIR),$(SRC_FILES)):
	@mkdir -p $(SRC_DIR)
	wget --no-use-server-timestamps -c -P $(SRC_DIR) $${SRC_URLS}

mirror: $(addprefix $(SRC_DIR),$(SRC_FILES))
