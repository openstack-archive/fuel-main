
$(call assert-variable,iso.path)
# $(call assert-variable,centos.path)

LEVEL ?= INFO
INSTALLATION_TIMEOUT ?= 1800
CHEF_TIMEOUT ?= 600

/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

clean: clean-integration-test


.PHONY: test-integration
test-integration: $/environment-id-integration
	python test/integration_test.py -l $(LEVEL) --installation-timeout=$(INSTALLATION_TIMEOUT) --chef-timeout=$(CHEF_TIMEOUT) --cache-file $(abspath $<) --iso $(abspath $(iso.path)) test $(NOSEARGS)

$/environment-id-integration: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) destroy
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) --iso $(abspath $(iso.path)) setup

.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	test -f $/environment-id-integration.candidate && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-integration.candidate) destroy || true
	test -f $/environment-id-integration && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-integration) destroy || true



