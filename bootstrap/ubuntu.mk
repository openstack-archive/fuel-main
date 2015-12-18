.PHONY: bootstrap-ubuntu

$(BUILD_DIR)/bootstrap/fuel-bootstrap-image-builder-rpm.done: top_builddir:=$(BUILD_DIR)/ubuntu-bootstrap/fuel-bootstrap-image-builder
$(BUILD_DIR)/bootstrap/fuel-bootstrap-image-builder-rpm.done: $(SOURCE_DIR)/fuel-bootstrap-image-builder/Makefile
	mkdir -p $(top_builddir)
	$(MAKE) -C $(SOURCE_DIR)/fuel-bootstrap-image-builder rpm top_builddir=$(top_builddir) VERSION=$(PRODUCT_VERSION).0
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS
	find $(top_builddir) -type f -name '*.rpm' | \
		xargs cp -a --target-directory=$(BUILD_DIR)/packages/rpm/RPMS
	$(ACTION.TOUCH)

bootstrap-ubuntu: $(BUILD_DIR)/bootstrap/fuel-bootstrap-image-rpm.done

