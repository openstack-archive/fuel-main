
APT_CONF_TEMPLATES := apt-ftparchive-deb.conf apt-ftparchive-udeb.conf apt-ftparchive-release.conf Release-amd64
empty_line:=
define insert_ubuntu_version
	sed -i $(1) \
		-e 's|@@UBUNTU_RELEASE@@|$(UBUNTU_RELEASE)|g' \
		-e 's|@@UBUNTU_RELEASE_NUMBER@@|$(UBUNTU_RELEASE_NUMBER)|g'
	$(empty_line)
endef

ifeq (,$(findstring clean,$(MAKECMDGOALS)))
include $(BUILD_DIR)/ubuntu_installer_kernel_version.mk
endif

define newline


endef
# there are two blank lines here, this is not an error

define apt_sources_list
$(if $(subst none,,$(USE_MIRROR)),
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main,
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main universe multiverse restricted
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-updates main universe multiverse restricted
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-security main universe multiverse restricted
deb $(MIRROR_UBUNTU_SECURITY) $(UBUNTU_RELEASE)-security main universe multiverse restricted
deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main
)
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb ,deb $(EXTRA_DEB_REPOS)))
endef

define policy_rc_d
#!/bin/sh
# suppress starting services in the staging chroot
exit 101
endef

$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export APT_SOURCES_LIST:=$(apt_sources_list)
$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export POLICY_RC_D:=$(policy_rc_d)
$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export CHROOT_DIR:=$(BUILD_DIR)/mirror/ubuntu/chroot

$(BUILD_DIR)/mirror/ubuntu/createchroot.done:
	mkdir -p $(CHROOT_DIR)
	# Prevent services from being started inside the staging chroot
	policy_rc_d="$(CHROOT_DIR)/usr/sbin/policy-rc.d"; \
	mkdir -p "$${policy_rc_d%/*}"; \
	echo "$${POLICY_RC_D}" > "$${policy_rc_d}"; \
	chmod 755 "$${policy_rc_d}"
	mkdir -p $(CHROOT_DIR)/etc/init.d
	# Avoid base packages' configuration errors by preventing the postinst
	# scripts from fiddling with the services' start order.
	# Suppresses the scary error messages
	# "Errors were while processing: <long-list-of-base-packages>'
	# and makes it possible to install non-trivial packages in the chroot
	touch $(CHROOT_DIR)/etc/init.d/.legacy-bootordering
	# copy the mirroring script and the list of the packages
	mkdir -p $(CHROOT_DIR)/repo
	rsync -a $(SOURCE_DIR)/mirror/ubuntu/files/ $(CHROOT_DIR)/repo/
	cp -a $(SOURCE_DIR)/requirements-deb.txt $(CHROOT_DIR)
	$(foreach f,$(APT_CONF_TEMPLATES),$(call insert_ubuntu_version,$(CHROOT_DIR)/repo/$(f)))
	chmod +x $(CHROOT_DIR)/repo/mkrepo.sh
	# bootstrap Ubuntu
	sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) \
		--variant=minbase --include=apt-utils,wget,bzip2,make \
		$(UBUNTU_RELEASE) $(CHROOT_DIR) $(MIRROR_UBUNTU)
	sudo rm -f $(CHROOT_DIR)/etc/apt/sources.list.d/*.list
	echo "$${APT_SOURCES_LIST}" | sudo tee $(CHROOT_DIR)/etc/apt/sources.list
	echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(CHROOT_DIR)/etc/apt/apt.conf.d/02mirantis-unauthenticated
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/files/preferences $(CHROOT_DIR)/etc/apt
	sudo rm -f $(CHROOT_DIR)/etc/resolv.conf
	sudo cp /etc/resolv.conf $(CHROOT_DIR)/etc/resolv.conf
	extra_env=""; \
	if [ -n "$$HTTP_PROXY" ] || [ -n "$$http_proxy" ]; then \
		HTTP_PROXY="$${HTTP_PROXY:-$${http_proxy}}"; \
		echo "Acquire::http { Proxy \"$$HTTP_PROXY\"; };" | sudo tee $(CHROOT_DIR)/etc/apt/apt.conf.d/03-use-proxy; \
		extra_env="HTTP_PROXY=$${HTTP_PROXY} http_proxy=$${HTTP_PROXY}"; \
	fi; \
	sudo chroot $(CHROOT_DIR) env \
		UBUNTU_RELEASE='$(UBUNTU_RELEASE)' \
		UBUNTU_INSTALLER_KERNEL_VERSION='$(UBUNTU_INSTALLER_KERNEL_VERSION)' \
		UBUNTU_KERNEL_FLAVOR='$(UBUNTU_KERNEL_FLAVOR)' \
		$$extra_env \
		/repo/mkrepo.sh
	rsync -a --delete $(CHROOT_DIR)/repo/pool/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/
	rsync -a --delete $(CHROOT_DIR)/repo/dists/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/dists/
	rsync -a --delete $(CHROOT_DIR)/repo/indices/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/indices/
	$(ACTION.TOUCH)
