$(BUILD_DIR)/mirror/ubuntu/createchroot.done: 
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
#	sudo debootstrap --components=main,universe $(UBUNTU_RELEASE) $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot $(shell echo $(MIRROR_UBUNTU) | sed 's/.dists\///g')
	sudo debootstrap --components=main,universe --include=germinate,reprepro $(UBUNTU_RELEASE) $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot http://mirror.yandex.ru/ubuntu
#	echo deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/mirantis.list
	echo deb http://download.mirantis.com/precise-grizzly-fuel-3.2 $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/mirantis.list
	echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/apt.conf.d/02mirantis-unauthenticated
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "echo germinate"
	sed 's/^/\ \* /g' $(SOURCE_DIR)/requirements-deb.txt | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/requirements.txt
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/resolvedep/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	$(ACTION.TOUCH)
