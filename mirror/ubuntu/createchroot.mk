$(BUILD_DIR)/mirror/ubuntu/createchroot.done: 
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
#	sudo debootstrap --components=main,universe $(UBUNTU_RELEASE) $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot $(shell echo $(MIRROR_UBUNTU) | sed 's/.dists\///g')
	sudo debootstrap --include=wget --components=main,universe $(UBUNTU_RELEASE) $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot http://mirror.yandex.ru/ubuntu
#	echo deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/mirantis.list
	echo deb http://srv08-srt.srt.mirantis.net/ubuntu-repo/precise-grizzly-fuel-3.2 $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/mirantis.list
	echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/apt.conf.d/02mirantis-unauthenticated
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/preferences $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "apt-get update && apt-get -dy install $(shell echo $(REQUIRED_DEBS) | tr '\n' ' ')"
	sudo mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/mkrepo.sh $(SOURCE_DIR)/mirror/ubuntu/apt-ftparchive-deb.conf $(SOURCE_DIR)/mirror/ubuntu/apt-ftparchive-udeb.conf $(SOURCE_DIR)/mirror/ubuntu/apt-ftparchive-release.conf $(SOURCE_DIR)/mirror/ubuntu/Release-amd64 $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "chmod +x /repo/mkrepo.sh && /repo/mkrepo.sh"
	sudo mv $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/* $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ && sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	$(ACTION.TOUCH)
