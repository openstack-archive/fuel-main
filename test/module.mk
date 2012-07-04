
$(call assert-variable,iso.path)

LEVEL ?= INFO


/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

clean: clean-integration-test


.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	test -f $/environment-id.candidate && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id.candidate) destroy || true
	test -f $/environment-id && \
		python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $/environment-id) destroy || true

.PHONY: test-integration
test-integration: $/environment-id
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $<) --iso $(abspath $(iso.path)) test

$/environment-id: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) destroy
	python test/integration_test.py -l $(LEVEL) --cache-file $(abspath $@) --iso $(abspath $(iso.path)) setup

