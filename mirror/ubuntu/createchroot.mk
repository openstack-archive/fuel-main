
ifeq (,$(findstring clean,$(MAKECMDGOALS)))
include $(BUILD_DIR)/ubuntu_installer_kernel_version.mk
endif

$(BUILD_DIR)/mirror/ubuntu/createchroot.done:
	sed $(SOURCE_DIR)/mirror/ubuntu/files/repo.sh.in \
		-e "s|@USE_MIRROR@|$(USE_MIRROR)|g" \
		-e "s|@MIRROR_UBUNTU@|$(MIRROR_UBUNTU)|g" \
		-e "s|@MIRROR_FUEL_UBUNTU@|$(MIRROR_FUEL_UBUNTU)|g" \
		-e "s|@UBUNTU_RELEASE@|$(UBUNTU_RELEASE)|g" \
		-e "s|@UBUNTU_INSTALLER_KERNEL_VERSION@|$(UBUNTU_INSTALLER_KERNEL_VERSION)|g" \
		-e "s|@UBUNTU_KERNEL_FLAVOR@|$(UBUNTU_KERNEL_FLAVOR)|g" \
		> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/repo.sh
	sudo docker run --rm \
		-v $(LOCAL_MIRROR_UBUNTU_OS_BASEURL):/root/.aptly \
		-v $(SOURCE_DIR)/mirror/ubuntu/files:/mnt \
		-v $(SOURCE_DIR)/requirements-deb.txt:/requirements-deb.txt \
		ubuntu:$(UBUNTU_RELEASE) /bin/bash -l /root/.aptly/repo.sh
	$(ACTION.TOUCH)
