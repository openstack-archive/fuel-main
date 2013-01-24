NAILGUN_VERSION:=$(shell python -c "import sys; sys.path.insert(0, '$(SOURCE_DIR)/nailgun'); import setup; print setup.version")

$(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz: \
		$(call find-files,$(SOURCE_DIR)/nailgun)
	cd $(SOURCE_DIR)/nailgun && \
	python setup.py sdist --dist-dir $(BUILD_DIR)/packages/eggs

test-unit: test-unit-nailgun

.PHONY: test-unit test-unit-nailgun
test-unit-nailgun:
	cd $(SOURCE_DIR)/nailgun && ./run_tests.sh
