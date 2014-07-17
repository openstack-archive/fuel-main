.PHONY: all puppet

all: puppet

########################
# PUPPET ARTIFACT
########################
PUPPET_ART_NAME:=puppet.tgz
puppet: $(ARTS_DIR)/$(PUPPET_ART_NAME)

$(ARTS_DIR)/$(PUPPET_ART_NAME): $(BUILD_DIR)/puppet/$(PUPPET_ART_NAME)
	$(ACTION.COPY)

PUPPET_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(PUPPET_ART_NAME))

ifdef PUPPET_DEP_FILE
$(BUILD_DIR)/puppet/$(PUPPET_ART_NAME): $(PUPPET_DEP_FILE)
	$(ACTION.COPY)
else
$(BUILD_DIR)/puppet/$(PUPPET_ART_NAME): \
		$(BUILD_DIR)/repos/fuellib.done \
		$(call find-files,$(BUILD_DIR)/repos/fuellib/deployment/puppet)
	mkdir -p $(@D)
	tar czf $@ -C $(BUILD_DIR)/repos/fuellib/deployment puppet
endif
