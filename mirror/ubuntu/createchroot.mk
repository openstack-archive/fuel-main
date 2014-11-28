
APT_CONF_TEMPLATES := apt-ftparchive-deb.conf apt-ftparchive-udeb.conf apt-ftparchive-release.conf Release-amd64
empty_line:=
define insert_ubuntu_version
	sudo sed -i $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/$(1) \
		-e 's|@@UBUNTU_RELEASE@@|$(UBUNTU_RELEASE)|g' \
		-e 's|@@UBUNTU_RELEASE_NUMBER@@|$(UBUNTU_RELEASE_NUMBER)|g'
	$(empty_line)
endef

$(BUILD_DIR)/mirror/ubuntu/createchroot.done: $(BUILD_DIR)/mirror/ubuntu/boot.done
$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export UBUNTU_INSTALLER_KERNEL_VERSION=$(strip $(patsubst lib/modules/%/kernel,%,$(shell zcat $(LOCAL_NETBOOT_DIR)/ubuntu-installer/amd64/initrd.gz | cpio --list 'lib/modules/*/kernel')))
$(BUILD_DIR)/mirror/ubuntu/createchroot.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc
	cp $(SOURCE_DIR)/mirror/ubuntu/multistrap.conf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/
	sed -i $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf \
		-e 's|@@MIRROR_UBUNTU@@|$(MIRROR_UBUNTU)|g' \
		-e 's|@@MIRROR_FUEL_UBUNTU@@|$(MIRROR_FUEL_UBUNTU)|g' \
		-e 's|@@UBUNTU_RELEASE@@|$(UBUNTU_RELEASE)|g' \
		-e 's|@@UBUNTU_RELEASE_NUMBER@@|$(UBUNTU_RELEASE_NUMBER)|g'
ifneq (none,$(strip $(USE_MIRROR)))
	sed -i $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf \
		-e '/#ifdef USE_MIRROR_NONE/,/#endif/ { d }'
endif
	if [ -n "$(EXTRA_DEB_REPOS)" ]; then \
		extra_count=0; \
		extra_repos=""; \
		IFS='|'; \
		l='$(EXTRA_DEB_REPOS)'; \
		set -- $$l; unset IFS; \
		for repo; do \
			[ -z "$$repo" ] && continue; \
			extra_repo=Extra$$extra_count; \
			echo "[$$extra_repo]"; \
			echo "omitdebsrc=true"; \
			case $$repo in \
			    */) repo=$$repo/; \
				echo "source=$$repo"; \
				;; \
			    *)  set -- $$repo; \
				if [ $$# -lt 3 ]; then \
				    echo Incorrect repo \"$$repo\" >&2; \
				    exit 1; \
				fi; \
				url=$$1; \
				suite=$$2; \
				shift; shift; \
				components="$$@"; \
				echo "source=$$url"; \
				echo "suite=$$suite"; \
				echo "components=$$components"; \
			    ;; \
			esac; \
			extra_count=$$(($$extra_count + 1)); \
			extra_repos="$$extra_repos $$extra_repo"; \
		done >> $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
		sed -i -e "s/\(bootstrap\|aptsources\)=.*/\0 $$extra_repos/g" $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/multistrap.conf; \
	fi
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
	$(foreach f,$(APT_CONF_TEMPLATES),$(call insert_ubuntu_version,$(f)))
	sudo chmod +x $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/mkrepo.sh
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot env \
		UBUNTU_RELEASE='$(UBUNTU_RELEASE)' \
		UBUNTU_INSTALLER_KERNEL_VERSION='$(UBUNTU_INSTALLER_KERNEL_VERSION)' \
		UBUNTU_KERNEL_FLAVOR='$(UBUNTU_KERNEL_FLAVOR)' \
		/repo/mkrepo.sh
	sudo rsync -a --delete $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/* $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ && sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/
	$(ACTION.TOUCH)
