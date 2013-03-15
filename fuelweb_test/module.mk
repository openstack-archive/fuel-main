
$(call assert-variable,iso.path)
# $(call assert-variable,centos.path)

LEVEL ?= INFO

NOFORWARD ?= 0
ifeq ($(NOFORWARD),1)
NOFORWARD_CLI_ARG=--no-forward-network
else
NOFORWARD_CLI_ARG=
endif

ifeq ($(ENV_NAME),)
ENV_NAME_CLI_ARG=
else
ENV_NAME_CLI_ARG=--environment "$(ENV_NAME)"
endif

INSTALLATION_TIMEOUT ?= 1800
DEPLOYMENT_TIMEOUT ?= 1800

/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

.PHONY: test-integration test-integration-env
test-integration: test-integration-env
	python fuelweb_test/integration_test.py -l $(LEVEL) $(ENV_NAME_CLI_ARG) --installation-timeout=$(INSTALLATION_TIMEOUT) \
		--deployment-timeout=$(DEPLOYMENT_TIMEOUT) --iso $(abspath $(iso.path)) test $(NOSEARGS)

test-integration-env: $(BUILD_DIR)/iso/iso.done
	@mkdir -p $(@D)
	python fuelweb_test/integration_test.py -l $(LEVEL) $(ENV_NAME_CLI_ARG) destroy
	python fuelweb_test/integration_test.py -l $(LEVEL) $(ENV_NAME_CLI_ARG) $(NOFORWARD_CLI_ARG) --iso $(abspath $(iso.path)) setup

.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	python fuelweb_test/integration_test.py -l $(LEVEL) $(ENV_NAME_CLI_ARG) destroy
