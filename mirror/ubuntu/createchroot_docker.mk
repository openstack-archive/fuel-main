$(BUILD_DIR)/mirror/ubuntu/createchroot.done: \
		$(BUILD_DIR)/docker/base-images.done

	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt
	echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main > $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/ubuntu.list
	if [ "$(USE_MIRROR)" = "none" ]; then \
		echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) universe multiverse restricted >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/ubuntu.list; \
		echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-updates main universe multiverse restricted >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/ubuntu.list; \
		echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-security main universe multiverse restricted >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/ubuntu.list; \
		echo deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main > $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/mirantis.list; \
	fi
	echo 'APT::Get::AllowUnauthenticated 1;' > $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/02mirantis-unauthenticated
	[ -n "$(EXTRA_DEB_REPOS)" ] && echo "$(EXTRA_DEB_REPOS)" | tr '|' '\n' | while read repo; do echo deb $$repo; done  | tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/extra.list || exit 0

	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo
	rsync -a $(SOURCE_DIR)/mirror/ubuntu/files/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/

	chmod +x $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/mkrepo.sh

	docker run -v $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/:/repo \
						 -v $(SOURCE_DIR)/mirror/ubuntu/files/preferences:/etc/apt/preferences \
						 -v $(SOURCE_DIR)/requirements-deb.txt:/requirements-deb.txt \
						 -v $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/apt/:/etc/apt/sources.list.d \
						 -v $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/02mirantis-unauthenticated:/etc/apt/apt.conf.d/02mirantis-unauthenticated \
						 -t -i fuel/ubuntu /repo/mkrepo.sh


	sudo rsync -a --delete $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/* $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ && sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	$(ACTION.TOUCH)
