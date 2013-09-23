SHOTGUN_VERSION:=$(shell python -c "import sys; sys.path.insert(0, '$(SOURCE_DIR)/shotgun'); import setup; print setup.version")

$(BUILD_DIR)/packages/eggs/Shotgun-$(SHOTGUN_VERSION).tar.gz: $(call find-files,$(SOURCE_DIR)/shotgun)
	cd $(SOURCE_DIR)/shotgun && \
		python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs

