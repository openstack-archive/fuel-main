
APT_CONF_TEMPLATES := apt-ftparchive-deb.conf apt-ftparchive-udeb.conf apt-ftparchive-release.conf Release-amd64
empty_line:=
define insert_ubuntu_version
	sed -i $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/$(1) \
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
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb,deb $(EXTRA_DEB_REPOS)))
endef

define policy_rc_d
#!/bin/sh
# suppress starting services in the staging chroot
exit 101
endef

$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export APT_SOURCES_LIST:=$(apt_sources_list)
$(BUILD_DIR)/mirror/ubuntu/createchroot.done: export POLICY_RC_D:=$(policy_rc_d)

$(BUILD_DIR)/mirror/ubuntu/createchroot.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	# Prevent services from being started inside the staging chroot
	policy_rc_d="$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/usr/sbin/policy-rc.d"; \
	mkdir -p "$${policy_rc_d%/*}"; \
	echo "$${POLICY_RC_D}" > "$${policy_rc_d}"; \
	chmod 755 "$${policy_rc_d}"
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/init.d
	# Avoid base packages' configuration errors by preventing the postinst
	# scripts from fiddling with the services' start order.
	# Suppresses the scary error messages
	# "Errors were while processing: <long-list-of-base-packages>'
	# and makes it possible to install non-trivial packages in the chroot
	touch $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/init.d/.legacy-bootordering
	# copy the mirroring script and the list of the packages
	mkdir -p $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo
	rsync -a $(SOURCE_DIR)/mirror/ubuntu/files/ $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/
	cp -a $(SOURCE_DIR)/requirements-deb.txt $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	$(foreach f,$(APT_CONF_TEMPLATES),$(call insert_ubuntu_version,$(f)))
	chmod +x $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/mkrepo.sh
	# bootstrap Ubuntu
	sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) \
		--variant=minbase --include=apt-utils,wget,bzip2,curl \
		$(UBUNTU_RELEASE) $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot $(MIRROR_UBUNTU)
	sudo rm -f $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list.d/*.list
	echo "$${APT_SOURCES_LIST}" | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/sources.list
	echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/apt.conf.d/02mirantis-unauthenticated
	sudo cp -a $(SOURCE_DIR)/mirror/ubuntu/files/preferences $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt
	sudo rm -f $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/resolv.conf
	sudo cp /etc/resolv.conf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/resolv.conf
	extra_env=""; \
	if [ -n "$$HTTP_PROXY" ] || [ -n "$$http_proxy" ]; then \
		HTTP_PROXY="$${HTTP_PROXY:-$${http_proxy}}"; \
		echo "Acquire::http { Proxy \"$$HTTP_PROXY\"; };" | sudo tee $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/etc/apt/apt.conf.d/03-use-proxy; \
		extra_env="HTTP_PROXY=$${HTTP_PROXY} http_proxy=$${HTTP_PROXY}"; \
	fi; \
	sudo chroot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot env \
		MIRROR_UBUNTU='$(MIRROR_UBUNTU)' \
		UBUNTU_RELEASE='$(UBUNTU_RELEASE)' \
		UBUNTU_ARCH='$(UBUNTU_ARCH)' \
		UBUNTU_INSTALLER_KERNEL_VERSION='$(UBUNTU_INSTALLER_KERNEL_VERSION)' \
		UBUNTU_KERNEL_FLAVOR='$(UBUNTU_KERNEL_FLAVOR)' \
		UBUNTU_RELEASE_FULL='$(UBUNTU_MAJOR).$(UBUNTU_MINOR).$(UBUNTU_UPDATE)' \
		$$extra_env \
		/repo/mkrepo.sh
	sudo rsync -a --delete $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/repo/* $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/
	sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot
	$(ACTION.TOUCH)
