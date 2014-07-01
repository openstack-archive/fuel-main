.PHONY: image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

########################
# TARGET IMAGE ARTIFACT
########################

image: target_centos_image target_ubuntu_image
