define build_container
$(BUILD_DIR)/docker/$1.done: $(BUILD_DIR)/repos/fuellib.done
$(BUILD_DIR)/docker/build.done: $(BUILD_DIR)/docker/$1.done

$(BUILD_DIR)/docker/$1.done:
	mkdir -p "$(BUILD_DIR)/docker/containers"
	rm -rf $(BUILD_DIR)/docker/$1
	cp -a $(SOURCE_DIR)/docker/$1 $(BUILD_DIR)/docker/$1
	mkdir -p $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	rsync -a $(BUILD_DIR)/repos/fuellib/deployment/puppet/* $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	sudo docker build -t fuel/$1 $(BUILD_DIR)/docker/$1
	docker save fuel/$1 > $(BUILD_DIR)/docker/containers/$1.tar
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/docker/build.done:
	tar cv $(BUILD_DIR)/docker/containers/*.tar | lrzip > $(BUILD_DIR)/docker/fuel-images.tar.lrz	
	$(ACTION.TOUCH)

$(eval $(call build_container,rabbitmq))
