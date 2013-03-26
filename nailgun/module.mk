NAILGUN_VERSION:=$(shell python -c "import sys; sys.path.insert(0, '$(SOURCE_DIR)/nailgun'); import setup; print setup.version")

$(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz: $(call depv,NO_UI_OPTIMIZE) \
		$(call find-files,$(SOURCE_DIR)/nailgun)
ifeq ($(NO_UI_OPTIMIZE),0)
	mkdir -p $(BUILD_DIR)/packages/eggs
	cp -r $(SOURCE_DIR)/nailgun $(BUILD_DIR)/packages/eggs
	cd $(SOURCE_DIR)/nailgun && \
		r.js -o build.js dir=$(BUILD_DIR)/packages/eggs/nailgun/static
	rm -rf $(BUILD_DIR)/packages/eggs/nailgun/static/templates
	rm -rf $(BUILD_DIR)/packages/eggs/nailgun/static/build.txt
	find $(BUILD_DIR)/packages/eggs/nailgun/static/css -type f ! -name main.css -delete
	find $(BUILD_DIR)/packages/eggs/nailgun/static/js -type f ! -name main.js -and ! -name require.js -delete
	cd $(BUILD_DIR)/packages/eggs/nailgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs
else
	cd $(SOURCE_DIR)/nailgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs
endif

test-unit: test-unit-nailgun

.PHONY: test-unit test-unit-nailgun
test-unit-nailgun:
	cd $(SOURCE_DIR)/nailgun && ./run_tests.sh
