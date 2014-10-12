$(BUILD_DIR)/mirror/ubuntu/createchroot.done: 
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc
	cp $(SOURCE_DIR)/mirror/ubuntu/multistrap.conf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/
	if [ "$(USE_MIRROR)" = "none" ]; then \
	echo "[Security]" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "source=@@MIRROR_UBUNTU@@" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "suite=@@UBUNTU_RELEASE@@-security" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "omitdebsrc=true" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "[Ubuntu]" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "source=@@MIRROR_UBUNTU@@" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "suite=@@UBUNTU_RELEASE@@" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "omitdebsrc=true" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "[Updates]" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "source=@@MIRROR_UBUNTU@@" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "suite=@@UBUNTU_RELEASE@@-updates" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	echo "omitdebsrc=true" >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	fi
	sed -i -e "s/@@UBUNTU_RELEASE@@/$(UBUNTU_RELEASE)/g" $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf
	sed -i -e "s]@@MIRROR_UBUNTU@@]$(MIRROR_UBUNTU)]g" $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf
	mount | grep -q $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc || sudo mount -t proc none $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc
	sudo multistrap -a amd64  -f $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf -d $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "dpkg --configure -a || exit 0"
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "rm -rf /var/run/*"
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "dpkg --configure -a || exit 0"
	sudo umount $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc
	sudo rm -f $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/*.list
	echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/ubuntu.list
	if [ "$(USE_MIRROR)" = "none" ]; then \
	echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) universe multiverse restricted | sudo tee -a $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/ubuntu.list; \
	echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-updates main universe multiverse restricted | sudo tee -a $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/ubuntu.list; \
	echo deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-security main universe multiverse restricted | sudo tee -a $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/ubuntu.list; \
	echo deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/mirantis.list; \
	fi
	echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/apt.conf.d/02mirantis-unauthenticated
	[ -n "$(EXTRA_DEB_REPOS)" ] && echo "$(EXTRA_DEB_REPOS)" | tr '|' '\n' | while read repo; do echo deb $$repo; done  | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/extra.list || exit 0
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/files/preferences $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt
	sudo cp -a $(SOURCE_DIR)/requirements-deb.txt $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	sudo cp /etc/resolv.conf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/resolv.conf
	sudo mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo
	sudo rsync -a $(SOURCE_DIR)/mirror/ubuntu/files/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/
	sudo chmod +x $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/mkrepo.sh
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot /bin/bash -c "export UBUNTU_RELEASE='$(UBUNTU_RELEASE)' UBUNTU_INSTALLER_KERNEL_VERSION='$(UBUNTU_INSTALLER_KERNEL_VERSION)'; /repo/mkrepo.sh"
	sudo rsync -a --delete $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/* $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ && sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	$(ACTION.TOUCH)
