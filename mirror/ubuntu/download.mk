.PHONY: mos-plus mos-ubuntu

mos-plus:
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/mos-plus
	wget -nv -nH -m -c --cut-dirs=3 --no-parent --reject "index.html*" -P $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/mos-plus $(MIRROR_UBUNTU)/mos-plus/

mos-ubuntu:
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/mos-ubuntu
	wget -nv -nH -m -c --cut-dirs=3 --no-parent --reject "index.html*" -P $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/mos-ubuntu $(MIRROR_UBUNTU)/mos-ubuntu/

$(BUILD_DIR)/mirror/ubuntu/download.done: mos-plus mos-ubuntu
		$(ACTION.TOUCH)
