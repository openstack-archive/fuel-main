
/:=$(BUILD_DIR)/test/

$(call assert-variable,iso.path)

test: test-integration

.PHONY: test-integration
test-integration: $/environment-id
	python test/integration.py -l INFO --cache-file $(abspath $/environment-id) test

$/environment-id: | $(iso.path)
	@mkdir -p $(@D)
	python test/integration.py -l INFO --cache-file $(abspath $@) destroy && rm -f $@
	python test/integration.py -l INFO --cache-file $(abspath $@) --iso $(abspath $(iso.path)) setup

