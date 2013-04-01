test: test-integration

.PHONY: test-integration
test-integration: $(BUILD_DIR)/iso/iso.done
	 ENV_NAME=$(ENV_NAME) ISO=$(abspath $(ISO_PATH)) LOGS_DIR=$(LOGS_DIR) nosetests -l $(LEVEL) $(NOSEARGS) -w $(SOURCE_DIR)/fuelweb_test/integration --with-xunit -s

.PHONY: clean-integration-test
clean-integration-test: /:=$/
clean-integration-test:
	dos.py erase $(ENV_NAME) || true