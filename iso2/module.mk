
/:=$(BUILD_DIR)/iso/

.PHONY: iso
iso: $/nailgun-ubuntu-12.04-amd64.iso

$(if $(BINARIES_DIR),,$(error BINARIES_DIR variable is not defined))
$(if $(gnupg.home),,$(error gnupg.home variable is not defined))

GEMS:=$(shell cd $(BINARIES_DIR)/gems && ls)
EGGS:=$(shell cd $(BINARIES_DIR)/eggs && ls)
EXTRA_PACKAGES:=$(shell grep -v ^\\s*\# requirements-deb.txt)
CACHED_EXTRA_PACKAGES:=$(shell cd $(BINARIES_DIR)/ubuntu/precise/extra && ls *.deb)

ISOROOT:=$/isoroot
ISO_IMAGE:=$(BINARIES_DIR)/ubuntu-12.04-server-amd64.iso
ISO_RELEASE:=precise
ISO_VERSION:=12.04
ISO_ARCHS:=i386 amd64
ISO_SECTIONS:=main restricted universe multiverse

UBUNTU_MIRROR:=http://ru.archive.ubuntu.com/ubuntu
OPSCODE_UBUNTU_MIRROR:=http://apt.opscode.com
UBUNTU_GPG_KEY1:=FBB75451 
UBUNTU_GPG_KEY2:=437D05B5 

$/%: /:=$/
$/%: ISOROOT:=$(ISOROOT)
$/%: ISO_RELEASE:=$(ISO_RELEASE)
$/%: ISO_VERSION:=$(ISO_VERSION)


$(BUILD_DIR)/ubuntu: $(BUILD_DIR)/ubuntu/md5sum.txt
$(BUILD_DIR)/ubuntu/%:
	mkdir -p $(@D)
	fuseiso $(ISO_IMAGE) $(@D)

clean: umount_ubuntu_image

.PHONY: umount_ubuntu_image
umount_ubuntu_image:
	-fusermount -u $(BUILD_DIR)/ubuntu


# DEBIAN PACKET CACHE RULES

APT_ROOT=$(abspath $/apt)

define apt_conf_contents
APT
{
  Architecture "amd64";
  Default-Release "$(ISO_RELEASE)";
  Get::AllowUnauthenticated "true";
};

Dir
{
  State "$(APT_ROOT)/state";
  State::status "status";
  Cache::archives "$(APT_ROOT)/archives";
  Cache "$(APT_ROOT)/cache";
  Etc "$(APT_ROOT)/etc";
};
endef

$/apt/etc/apt.conf: export contents:=$(apt_conf_contents)
$/apt/etc/apt.conf: | $/apt/etc/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


define apt_sources_list_contents
deb $(UBUNTU_MIRROR) precise main restricted universe multiverse
deb-src $(UBUNTU_MIRROR) precise main restricted universe multiverse
deb $(OPSCODE_UBUNTU_MIRROR) $(ISO_RELEASE)-0.10 main
endef

$/apt/etc/sources.list: export contents:=$(apt_sources_list_contents)
$/apt/etc/sources.list: | $/apt/etc/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


define opscode_preferences_contents
Package: *
Pin: origin "apt.opscode.com"
Pin-Priority: 999
endef

$/apt/etc/preferences.d/opscode: export contents:=$(opscode_preferences_contents)
$/apt/etc/preferences.d/opscode: | $/apt/etc/preferences.d/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


$/apt/state/status: | $/apt/state/.dir
	@mkdir -p $(@D)
	touch $@

$/apt-cache-infra.done: \
	  $/apt/etc/apt.conf \
		$/apt/etc/sources.list \
		$/apt/etc/preferences.d/opscode \
	  $/apt/archives/.dir \
		| $/apt/cache/.dir \
		  $/apt/state/status
	touch $@

$/apt-cache-iso.done: $(ISO_IMAGE) | $(BUILD_DIR)/ubuntu/pool $/apt/archives/.dir
	find $(abspath $(BUILD_DIR)/ubuntu/pool) -type f \( -name '*.deb' -o -name '*.udeb' \) -exec ln -sf {} $/apt/archives \;
	touch $@

$/apt-cache-index.done: $/apt-cache-infra.done
	apt-get -c=$/apt/etc/apt.conf update
	touch $@

$/apt-cache-extra.done: $/apt-cache-index.done $/apt-cache-iso.done requirements-deb.txt | $(addprefix $/apt/archives/,$(CACHED_EXTRA_PACKAGES))
	apt-get -c=$/apt/etc/apt.conf -d -y install $(EXTRA_PACKAGES)
	touch $@

$/apt/archives/%.deb: $(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/extra/%.deb
	ln -sf $(abspath $<) $@

$/apt-cache.done: $/apt-cache-extra.done


# UBUNTU KEYRING RULES

$/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg: $/apt-cache-index.done
	mkdir -p $/sources
	cd $/sources && \
		apt-get -c=$(abspath $/apt/etc/apt.conf) source ubuntu-keyring
	rm -rf $/ubuntu-keyring
	mv -T $$(find $/sources -name 'ubuntu-keyring*' -type d -maxdepth 1 | head -1) $/ubuntu-keyring
	rm -rf $/sources

$/ubuntu-mirantis-gnupg/%: $(gnupg.home)/%
	@mkdir -p $(@D)
	cp $< $@

$/ubuntu-mirantis-gnupg.done: $/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg $/ubuntu-mirantis-gnupg/pubring.gpg $/ubuntu-mirantis-gnupg/secring.gpg
	GNUPGHOME=$/ubuntu-mirantis-gnupg gpg --import < $<
	GNUPGHOME=$/ubuntu-mirantis-gnupg gpg --yes --export --output $< $(UBUNTU_GPG_KEY1) $(UBUNTU_GPG_KEY2) $(gnupg.default-key-id)
	touch $@

$/ubuntu-keyring.deb: $/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg $/ubuntu-mirantis-gnupg.done
	cd $/ubuntu-keyring && \
		dpkg-buildpackage -m"Mirantis Nailgun" -k"$(gnupg.default-key-id)" -uc -us
	cp $$(find $/ -name 'ubuntu-keyring_*.deb' | head -1) $@



# ISO ROOT RULES

$/isoroot-misc.done: $(ISO_IMAGE) | $(BUILD_DIR)/ubuntu
	mkdir -p $(ISOROOT)
	rsync --recursive --links --perms --chmod=u+w --exclude=pool $(BUILD_DIR)/ubuntu/ $(ISOROOT)
	touch $@

$/isoroot-pool.done: $/apt-cache.done
	mkdir -p $(ISOROOT)/pools/$(ISO_RELEASE)
	find $/apt/archives \( -name '*.deb' -o -name '*.udeb' \) | while read debfile; do \
    packname=`basename $${debfile} | cut -d_ -f1` ; \
    section=`grep -l "^$${packname}\s" $(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/indices/* | \
	    grep -v extra | head -1 | cut -d. -f3` ; \
    test -z $${section} && section=main ; \
    mkdir -p $(ISOROOT)/pools/$(ISO_RELEASE)/$${section} ; \
    cp -n $${debfile} $(ISOROOT)/pools/$(ISO_RELEASE)/$${section}/ ; \
  done
	touch $@


$/isoroot.done: \
	  $/isoroot-misc.done \
		$/isoroot-pool.done \
		$(foreach arch,$(ISO_ARCHS),\
		  $(foreach section,$(ISO_SECTIONS),\
			  $(ISOROOT)/dists/$(ISO_RELEASE)/$(section)/binary-$(arch)/Packages.gz \
				$(ISOROOT)/dists/$(ISO_RELEASE)/$(section)/debian-installer/binary-$(arch)/Packages.gz)) \
		$(foreach arch,$(ISO_ARCHS),\
		  $(foreach section,$(ISO_SECTIONS),\
			  $(ISOROOT)/dists/$(ISO_RELEASE)/$(section)/binary-$(arch)/Release)) \
		$(ISOROOT)/dists/$(ISO_RELEASE)/Release \
		$(ISOROOT)/bootstrap/linux \
		$(ISOROOT)/bootstrap/initrd.gz \
		$(addprefix $(ISOROOT)/gems/,$(GEMS)) \
		$(addprefix $(ISOROOT)/eggs/,$(EGGS))
		# $(ISOROOT)/dists/$(ISO_RELEASE)/Release.gpg \
	touch $@

$(ISOROOT)/md5sum.txt: $/isoroot.done
	cd $(@D) && find . -type f -print0 | \
	  xargs -0 md5sum | \
		grep -v "boot.cat" | \
		grep -v "md5sum.txt" > $(@F)

$(addprefix $(ISOROOT)/pools/$(ISO_RELEASE)/,$(ISO_SECTIONS)):
	mkdir -p $@

# Arguments:
#   1 - section (e.g. main, restricted, etc.)
#   2 - arch
#   3 - (optional) section subdirectory (empty or "/debian-installer")
define packages-build-rule-template
$(ISOROOT)/dists/$(ISO_RELEASE)/$1$3/binary-$2/Packages.gz: \
	  $/isoroot-pool.done \
	 	$(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/indices/override.$(ISO_RELEASE).$1
	mkdir -p $$(@D)
	cd $(ISOROOT) && \
		dpkg-scanpackages -m -a$2 \
			-t $(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/indices/override.$(ISO_RELEASE).$1$(3:/=.) \
			-e $(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/indices/override.$(ISO_RELEASE).extra.$1 \
			pools/$(ISO_RELEASE)/$1 \
			$(BINARIES_DIR)/ubuntu/$(ISO_RELEASE)/indices/override.$(ISO_RELEASE).$1 | gzip > $$(abspath $$@)
endef

packages-build-rule = $(eval $(call packages-build-rule-template,$1,$2,$3))

# Generate rules for building Packages index for all supported architectures
$(foreach section,$(ISO_SECTIONS),\
	$(foreach arch,$(ISO_ARCHS),\
    $(call packages-build-rule,$(section),$(arch),) \
    $(call packages-build-rule,$(section),$(arch),/debian-installer)))

# Arguments:
#   1 - section (e.g. main, restricted, etc.)
#   2 - arch
define release-build-rule-template
$(ISOROOT)/dists/$(ISO_RELEASE)/$1/binary-$2/Release:
	@mkdir -p $$(@D)
	echo "Archive: $(ISO_RELEASE)\nVersion: $(ISO_VERSION)\nComponent: $1\nOrigin: Mirantis\nLabel: Mirantis\nArchitecture: $2" > $$@
endef

release-build-rule = $(eval $(call release-build-rule-template,$1,$2))

$(foreach section,$(ISO_SECTIONS),\
  $(foreach arch,$(ISO_ARCHS),\
    $(call release-build-rule,$(section),$(arch))))


define release_conf_contents
APT::FTPArchive::Release::Origin "Mirantis";
APT::FTPArchive::Release::Label "Mirantis";
APT::FTPArchive::Release::Suite "$(ISO_RELEASE)";
APT::FTPArchive::Release::Version "$(ISO_VERSION)";
APT::FTPArchive::Release::Codename "$(ISO_RELEASE)";
APT::FTPArchive::Release::Architectures "$(ISO_ARCHS)";
APT::FTPArchive::Release::Components "$(ISO_SECTIONS)";
APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
endef

$/release.conf: export contents:=$(release_conf_contents)
$/release.conf:
	echo "$${contents}" > $@


$(ISOROOT)/dists/$(ISO_RELEASE)/Release: $/release.conf
	apt-ftparchive -c $< release $(ISOROOT)/dists/$(ISO_RELEASE) > $@

$(ISOROOT)/dists/$(ISO_RELEASE)/Release.gpg: $(ISOROOT)/dists/$(ISO_RELEASE)/Release
	GNUPGHOME=$(gnupg.home) gpg --yes --no-tty --default-key $(gnupg.default-key-id) --passphrase-file $(gnupg.keyphrase_file) --output $@ -ba $<


# MAIN ISO RULE

$/nailgun-ubuntu-12.04-amd64.iso: $/isoroot.done $(ISOROOT)/md5sum.txt
	mkisofs -r -V "Mirantis Nailgun" \
		-cache-inodes \
		-J -l -b isolinux/isolinux.bin \
		-c isolinux/boot.cat -no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-o $@ $(ISOROOT)

$(ISOROOT)/%: $(BINARIES_DIR)/%
	@mkdir -p $(@D)
	cp $< $@

