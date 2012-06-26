
$(call assert-variable,iso.path)


/:=$(BUILD_DIR)/test/

$/%: /:=$/

test: test-integration

clean: $/clean-integration-test-cache-file


.PHONY: $/clean-integration-test-cache-file
$/clean-integration-test-environment:
	test -f $/environment-id && \
		python test/integration.py -l INFO --cache-file $(abspath $/environment-id) destroy

.PHONY: test-integration
test-integration: $/environment-id
	python test/integration.py -l INFO --cache-file $(abspath $<) --iso $(abspath $(iso.path)) test

$/environment-id: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration.py -l INFO --cache-file $(abspath $@) destroy
	python test/integration.py -l INFO --cache-file $(abspath $@) --iso $(abspath $(iso.path)) setup

ifdef FORCE_INTEGRATION_ENVIRONMENT
$/environment-id: FORCE
endif
