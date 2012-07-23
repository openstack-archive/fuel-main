
$(call assert-variable,iso.path)
# $(call assert-variable,centos.path)

LEVEL ?= INFO
INSTALLATION_TIMEOUT ?= 1800
CHEF_TIMEOUT ?= 600

/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration test-cookbooks

clean: clean-integration-test clean-cookbooks-test


.PHONY: test-integration
test-integration: $/environment-id-integration
	python test/integration_test.py -l $(LEVEL) --installation-timeout=$(INSTALLATION_TIMEOUT) --chef-timeout=$(CHEF_TIMEOUT) --cache-file $(abspath $<) --iso $(abspath $(iso.path)) test

$/environment-id-integration: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) destroy
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) --iso $(abspath $(iso.path)) setup

.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	test -f $/environment-id.candidate && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-integration.candidate) destroy || true
	test -f $/environment-id && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-integration) destroy || true



.PHONY: test-cookbooks
test-cookbooks: $/environment-id-cookbooks
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $<) --iso $(image.centos.url) --suite cookbooks test

$/environment-id-cookbooks:
	@mkdir -p $(@D)
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) --suite cookbooks destroy
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) --iso $(image.centos.url) --suite cookbooks setup

.PHONY: clean-cookbooks-test
clean-cookbooks-test: /:=$/
clean-cookbooks-test:
	test -f $/environment-id-cookbooks.candidate && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-cookbooks.candidate) --suite cookbooks destroy || true
	test -f $/environment-id-cookbooks && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id-cookbooks) --suite cookbooks destroy || true

