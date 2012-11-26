
$(call assert-variable,iso.path)
# $(call assert-variable,centos.path)

LEVEL ?= INFO

NOFORWARD ?= 0
ifeq ($(NOFORWARD),1)
NOFORWARD_CLI_ARG=--no-forward-network
else
NOFORWARD_CLI_ARG=
endif

INSTALLATION_TIMEOUT ?= 1800
DEPLOYMENT_TIMEOUT ?= 1800

/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

.PHONY: test-integration
test-integration: $/environment-id-integration
	python test/integration_test.py -l $(LEVEL) --installation-timeout=$(INSTALLATION_TIMEOUT) --deployment-timeout=$(DEPLOYMENT_TIMEOUT) --iso $(abspath $(iso.path)) test $(NOSEARGS)

$/environment-id-integration: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration_test.py -l $(LEVEL) destroy
	python test/integration_test.py -l $(LEVEL) $(NOFORWARD_CLI_ARG) --iso $(abspath $(iso.path)) setup

.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	python test/integration_test.py -l $(LEVEL) destroy
