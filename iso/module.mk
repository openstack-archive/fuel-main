
/:=$(BUILD_DIR)/iso/

.PHONY: iso
all: iso
iso: $/nailgun-ubuntu-12.04-amd64.iso

ifndef BINARIES_DIR
$/%:
	$(error BINARIES_DIR variable is not defined)
else

$(call assert-variable,gnupg.home)

ISOROOT:=$/isoroot
UBUNTU_RELEASE:=$(UBUNTU_1204_RELEASE)
UBUNTU_VERSION:=$(UBUNTU_1204_VERSION)
UBUNTU_ARCHS:=i386 amd64
UBUNTU_SECTIONS:=main restricted universe multiverse

UBUNTU_GPG_KEY1:=FBB75451 
UBUNTU_GPG_KEY2:=437D05B5 

CENTOS_63_NETINST_ISO:=CentOS-$(CENTOS_63_RELEASE)-$(CENTOS_63_ARCH)-netinstall.iso
UBUNTU_NETINST_ISO:=$(UBUNTU_RELEASE)-x86_64.iso
ifeq ($(IGNORE_MIRROR),1)
CENTOS_63_NETINST_ISO_URL:=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/isos/$(CENTOS_63_ARCH)/$(CENTOS_63_NETINST_ISO)
UBUNTU_NETINST_ISO_URL:=http://archive.ubuntu.com/ubuntu/dists/precise/main/installer-amd64/current/images/netboot/mini.iso
else
CENTOS_63_NETINST_ISO_URL:=$(MIRROR_URL)/isos/$(CENTOS_63_NETINST_ISO)
UBUNTU_NETINST_ISO_URL:=$(MIRROR_URL)/isos/$(UBUNTU_NETINST_ISO)
endif
NETINST_ISOS:=$(CENTOS_63_NETINST_ISO) $(UBUNTU_NETINST_ISO)

ifdef MIRROR_DIR
ISOS_DIR:=$(MIRROR_DIR)/isos/
else
ISOS_DIR:=$(ISOROOT)/netinst/
endif

$(addprefix $(ISOS_DIR),$(NETINST_ISOS)):
	mkdir -p $(@D)
	curl -C - -o $(ISOS_DIR)$(CENTOS_63_NETINST_ISO) $(CENTOS_63_NETINST_ISO_URL)
	curl -C - -o $(ISOS_DIR)$(UBUNTU_NETINST_ISO) $(UBUNTU_NETINST_ISO_URL)

mirror: $(addprefix $(ISOS_DIR),$(NETINST_ISOS))

$/%: /:=$/
$/%: ISOROOT:=$(ISOROOT)
$/%: UBUNTU_RELEASE:=$(UBUNTU_RELEASE)
$/%: UBUNTU_VERSION:=$(UBUNTU_VERSION)


# UBUNTU KEYRING RULES

$/ubuntu-mirantis-gnupg/%: $(gnupg.home)/%
	$(ACTION.COPY)
	chmod 600 $@

$/ubuntu-mirantis-gnupg/.done: \
	  $/debian/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg \
		$/ubuntu-mirantis-gnupg/pubring.gpg \
		$/ubuntu-mirantis-gnupg/secring.gpg
	chmod 700 $(@D)
	GNUPGHOME=$/ubuntu-mirantis-gnupg gpg --import < $<
	GNUPGHOME=$/ubuntu-mirantis-gnupg gpg --yes --export --output $< $(UBUNTU_GPG_KEY1) $(UBUNTU_GPG_KEY2) $(gnupg.default-key-id)
	$(ACTION.TOUCH)

$/debian/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg: $(BINARIES_DIR)/ubuntu/precise/ubuntu-keyring.tar.gz
	rm -rf $/debian/ubuntu-keyring
	mkdir -p $/debian/ubuntu-keyring
	tar -xf $< --strip-components=1 -C $/debian/ubuntu-keyring
	find $/debian/ubuntu-keyring/ -type f -exec touch {} \;

$/debian/ubuntu-keyring/.done: $/debian/ubuntu-keyring/keyrings/ubuntu-archive-keyring.gpg $/ubuntu-mirantis-gnupg/.done
	cd $/debian/ubuntu-keyring && \
		dpkg-buildpackage -b -m"Mirantis Nailgun" -k"$(gnupg.default-key-id)" -uc -us
	$(ACTION.TOUCH)


# ISO ROOT RULES

$/isoroot-infra.done: $(UBUNTU_1204_ISO) | $(UBUNTU_1204_ROOT)
	mkdir -p $(ISOROOT)
	rsync --recursive --links --perms --chmod=u+w --exclude=pool $(UBUNTU_1204_ROOT)/ $(ISOROOT)
	scripts/mirror.sh $(GOLDEN_MIRROR) $(LOCAL_MIRROR)
	$(ACTION.TOUCH)

$/isoroot-pool.done: $(ubuntu.packages)/cache.done
	mkdir -p $(ISOROOT)/pools/$(UBUNTU_RELEASE)
	find $(ubuntu.packages)/archives \( -name '*.deb' -o -name '*.udeb' \) | while read debfile; do \
    packname=`basename $${debfile} | cut -d_ -f1` ; \
    section=`grep -l "^$${packname}\s" $(BINARIES_DIR)/ubuntu/$(UBUNTU_RELEASE)/indices/* | \
	    grep -v extra | head -1 | cut -d. -f3` ; \
    test -z $${section} && section=main ; \
    mkdir -p $(ISOROOT)/pools/$(UBUNTU_RELEASE)/$${section} ; \
    cp -n $${debfile} $(ISOROOT)/pools/$(UBUNTU_RELEASE)/$${section}/ ; \
  done
	$(ACTION.TOUCH)

$/isoroot-centos.done: $(centos.packages)/cache.done $(BUILD_DIR)/packages/rpm/rpm.done
	mkdir -p $(ISOROOT)/centos/$(CENTOS_63_RELEASE)
	find $(centos.packages)/Packages -name '*.rpm' -exec cp -n {} $(ISOROOT)/centos/$(CENTOS_63_RELEASE) \;
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -n {} $(ISOROOT)/centos/$(CENTOS_63_RELEASE) \;
	createrepo -g `readlink -f "$(centos.packages)/comps.xml"` -o $(ISOROOT)/centos/$(CENTOS_63_RELEASE) $(ISOROOT)/centos/$(CENTOS_63_RELEASE)
	$(ACTION.TOUCH)

$/isoroot-keyring.done: $/isoroot-pool.done $/debian/ubuntu-keyring/.done
	rm -rf $(ISOROOT)/pools/$(UBUNTU_RELEASE)/main/ubuntu-keyring*deb
	cp $/debian/ubuntu-keyring*deb $(ISOROOT)/pools/$(UBUNTU_RELEASE)/main/
	$(ACTION.TOUCH)

$/isoroot-packages.done: $/isoroot-pool.done $/isoroot-keyring.done
	$(ACTION.TOUCH)

$/isoroot-isolinux.done: $/isoroot-infra.done $(addprefix iso/stage/,$(call find-files,iso/stage))
	rsync -a iso/stage/ $(ISOROOT)
	$(ACTION.TOUCH)

$/isoroot.done: \
	  $/isoroot-infra.done \
	  $/isoroot-packages.done \
	  $/isoroot-centos.done \
		$/isoroot-isolinux.done \
		$(ISOROOT)/bootstrap/linux \
		$(ISOROOT)/bootstrap/initrd.gz \
		$(ISOROOT)/bootstrap/bootstrap.rsa \
		$(addprefix $(ISOROOT)/netinst/,$(NETINST_ISOS)) \
		$(ISOROOT)/bin/late \
		$(ISOROOT)/gnupg \
		$(addprefix $(ISOROOT)/gnupg/,$(call find-files,gnupg)) \
		$(ISOROOT)/sync \
		$(addprefix $(ISOROOT)/sync/,$(call find-files,iso/sync)) \
		$(addprefix $(ISOROOT)/indices/,$(call find-files,$(BINARIES_DIR)/ubuntu/$(UBUNTU_RELEASE)/indices)) \
		$(addprefix $(ISOROOT)/nailgun/,$(call find-files,nailgun)) \
		$(addprefix $(ISOROOT)/nailgun/bin/,create_release agent) \
		$(addprefix $(ISOROOT)/nailgun/solo/,solo.rb solo.json) \
		$(addprefix $(ISOROOT)/nailgun/cookbooks/,$(call find-files,cookbooks)) \
		$(addprefix $(ISOROOT)/nailgun/,openstack-essex.json) \
		$/isoroot-gems.done \
		$(ISOROOT)/eggs \
		$(addprefix $(ISOROOT)/eggs/,$(call find-files,$(LOCAL_MIRROR)/eggs)) \
		$(ISOROOT)/dists/$(UBUNTU_RELEASE)/Release \
		$(ISOROOT)/dists/$(UBUNTU_RELEASE)/Release.gpg
	$(ACTION.TOUCH)

$(ISOROOT)/md5sum.txt: $/isoroot.done
	cd $(@D) && find * -type f -print0 | \
	  xargs -0 md5sum | \
		grep -v "boot.cat" | \
		grep -v "md5sum.txt" > $(@F)


# Arguments:
#   1 - section (e.g. main, restricted, etc.)
#   2 - arch (e.g. i386, amd64)
#   3 - override path
#   4 - extra override path
define packages-build-rule-template
$(ISOROOT)/dists/$(UBUNTU_RELEASE)/$1/binary-$2/Packages: \
	  $/isoroot-packages.done \
		$(ISOROOT)/pools/$(UBUNTU_RELEASE)/$1 \
		$3 \
		$4
	mkdir -p $$(@D)
	cd $(ISOROOT) && \
		dpkg-scanpackages --multiversion --arch $2 --type deb \
			--extra-override $(abspath $4) pools/$(UBUNTU_RELEASE)/$1 $(abspath $3) > $$(abspath $$@)

$(ISOROOT)/dists/$(UBUNTU_RELEASE)/$1/debian-installer/binary-$2/Packages: \
	  $/isoroot-packages.done \
		$(ISOROOT)/pools/$(UBUNTU_RELEASE)/$1 \
		$3.debian-installer \
		$4
	mkdir -p $$(@D)
	cd $(ISOROOT) && \
		dpkg-scanpackages --multiversion --arch $2 --type udeb \
			--extra-override $(abspath $4) pools/$(UBUNTU_RELEASE)/$1 $(abspath $3.debian-installer) > $$(abspath $$@)
endef

packages-build-rule = $(eval $(call packages-build-rule-template,$1,$2,$3,$4))

# Generate rules for building Packages index for all supported architectures
#
# NOTE: section=main -- special case
INDICES_DIR:=$(BINARIES_DIR)/ubuntu/$(UBUNTU_RELEASE)/indices

$(foreach section,$(filter-out main,$(UBUNTU_SECTIONS)),\
	$(foreach arch,$(UBUNTU_ARCHS),\
    $(call packages-build-rule,$(section),$(arch),\
      $(INDICES_DIR)/override.$(UBUNTU_RELEASE).$(section),\
			$(INDICES_DIR)/override.$(UBUNTU_RELEASE).extra.$(section))))

$(foreach arch,$(UBUNTU_ARCHS),\
	$(call packages-build-rule,main,$(arch),\
	  $(INDICES_DIR)/override.$(UBUNTU_RELEASE).main,\
		$/override.$(UBUNTU_RELEASE).extra.main))

$/override.$(UBUNTU_RELEASE).extra.main: \
	  $(INDICES_DIR)/override.$(UBUNTU_RELEASE).extra.main \
		$(UBUNTU_1204_ROOT)/dists/$(UBUNTU_RELEASE)/main/binary-amd64/Packages.gz
	$(ACTION.COPY)
	gunzip -c $(filter %/Packages.gz,$^) | awk -F ": *" '$$1=="Package" {package=$$2} $$1=="Task" {print package " Task " $$2}' >> $@

# Arguments:
#   1 - section (e.g. main, restricted, etc.)
#   2 - arch
define release-build-rule-template
$(ISOROOT)/dists/$(UBUNTU_RELEASE)/$1/binary-$2/Release:
	@mkdir -p $$(@D)
	echo "Archive: $(UBUNTU_RELEASE)\nVersion: $(UBUNTU_VERSION)\nComponent: $1\nOrigin: Mirantis\nLabel: Mirantis\nArchitecture: $2" > $$@
endef

release-build-rule = $(eval $(call release-build-rule-template,$1,$2))

$(foreach section,$(UBUNTU_SECTIONS),\
  $(foreach arch,$(UBUNTU_ARCHS),\
    $(call release-build-rule,$(section),$(arch))))


define release_conf_contents
APT::FTPArchive::Release::Origin "Mirantis";
APT::FTPArchive::Release::Label "Mirantis";
APT::FTPArchive::Release::Suite "$(UBUNTU_RELEASE)";
APT::FTPArchive::Release::Version "$(UBUNTU_VERSION)";
APT::FTPArchive::Release::Codename "$(UBUNTU_RELEASE)";
APT::FTPArchive::Release::Architectures "$(UBUNTU_ARCHS)";
APT::FTPArchive::Release::Components "$(UBUNTU_SECTIONS)";
APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
endef

$/release.conf: export contents:=$(release_conf_contents)
$/release.conf:
	echo "$${contents}" > $@


$(addprefix $(ISOROOT)/pools/$(UBUNTU_RELEASE)/,$(UBUNTU_SECTIONS)):
	mkdir -p $@

$(ISOROOT)/dists/%.gz: $(ISOROOT)/dists/%
	gzip -c $< > $@

$(ISOROOT)/dists/$(UBUNTU_RELEASE)/Release: \
	  $/release.conf \
		$(foreach arch,$(UBUNTU_ARCHS),\
		  $(foreach section,$(UBUNTU_SECTIONS),\
			  $(ISOROOT)/dists/$(UBUNTU_RELEASE)/$(section)/binary-$(arch)/Packages \
			  $(ISOROOT)/dists/$(UBUNTU_RELEASE)/$(section)/binary-$(arch)/Packages.gz \
				$(ISOROOT)/dists/$(UBUNTU_RELEASE)/$(section)/debian-installer/binary-$(arch)/Packages \
				$(ISOROOT)/dists/$(UBUNTU_RELEASE)/$(section)/debian-installer/binary-$(arch)/Packages.gz \
			  $(ISOROOT)/dists/$(UBUNTU_RELEASE)/$(section)/binary-$(arch)/Release))
	apt-ftparchive -c $< release $(ISOROOT)/dists/$(UBUNTU_RELEASE) > $@

$(ISOROOT)/dists/$(UBUNTU_RELEASE)/Release.gpg: $(ISOROOT)/dists/$(UBUNTU_RELEASE)/Release
	GNUPGHOME=$(gnupg.home) gpg --yes --no-tty --default-key $(gnupg.default-key-id) --passphrase-file $(gnupg.keyphrase-file) --output $@ -ba $<

define late_contents
#!/bin/sh
# THIS SCRIPT IS FOR USING BY DEBIAN-INSTALLER ONLY

set -e

# repo
mkdir -p /target/var/lib/mirror/ubuntu
cp -r /cdrom/pools /target/var/lib/mirror/ubuntu
cp -r /cdrom/dists /target/var/lib/mirror/ubuntu
cp -r /cdrom/indices /target/var/lib/mirror/ubuntu
mkdir -p /target/etc/apt/sources.list.d
rm -f /target/etc/apt/sources.list
echo "deb file:/var/lib/mirror/ubuntu precise main restricted universe multiverse" > /target/etc/apt/sources.list.d/local.list

# rpm
mkdir -p /target/var/lib/mirror
cp -r /cdrom/centos /target/var/lib/mirror

# gnupg
cp -r /cdrom/gnupg /target/root/.gnupg
chown -R root:root /target/root/.gnupg
chmod 700 /target/root/.gnupg
chmod 600 /target/root/.gnupg/*

# bootstrap
mkdir -p /target/var/lib/mirror/bootstrap
cp /cdrom/bootstrap/linux /target/var/lib/mirror/bootstrap/linux
cp /cdrom/bootstrap/initrd.gz /target/var/lib/mirror/bootstrap/initrd.gz

mkdir -p /target/root
cp /cdrom/bootstrap/bootstrap.rsa /target/root/bootstrap.rsa
chmod 640 /target/root/bootstrap.rsa

# netinst
mkdir -p /target/var/lib/mirror/netinst
cp /cdrom/netinst/* /target/var/lib/mirror/netinst

# nailgun
mkdir -p /target/opt
cp -r /cdrom/nailgun /target/opt

#system
cp -r /cdrom/sync/* /target/
in-target update-rc.d chef-client disable

# eggs
cp -r /cdrom/eggs /target/var/lib/mirror

# gems
cp -r /cdrom/gems /target/var/lib/mirror

endef

$(ISOROOT)/bin/late: export contents:=$(late_contents)
$(ISOROOT)/bin/late:
	@mkdir -p $(@D)
	echo "$${contents}" > $@
	chmod +x $@



$/apt/state/%: $(BINARIES_DIR)/ubuntu/precise/state/% ; $(ACTION.COPY)

$(ISOROOT)/bootstrap/bootstrap.rsa: bootstrap/ssh/id_rsa ; $(ACTION.COPY)
ifeq ($(BOOTSTRAP_REBUILD),1)
$(ISOROOT)/bootstrap/%: $(BUILD_DIR)/bootstrap/% ; $(ACTION.COPY)
else
$(ISOROOT)/bootstrap/%: $(BINARIES_DIR)/bootstrap/% ; $(ACTION.COPY)
endif

$(ISOROOT)/gnupg:
	mkdir -p $@
$(ISOROOT)/gnupg/%: gnupg/% ; $(ACTION.COPY)
$(ISOROOT)/sync:
	mkdir -p $@
$(ISOROOT)/sync/%: iso/sync/% ; $(ACTION.COPY)
$(ISOROOT)/indices/override.$(UBUNTU_RELEASE).extra.main: $/override.$(UBUNTU_RELEASE).extra.main ; $(ACTION.COPY)
$(ISOROOT)/indices/%: $(BINARIES_DIR)/ubuntu/$(UBUNTU_RELEASE)/indices/% ; $(ACTION.COPY)
$(ISOROOT)/nailgun/cookbooks/%: cookbooks/% ; $(ACTION.COPY)
$(ISOROOT)/nailgun/openstack-essex.json: scripts/release/openstack-essex.json ; $(ACTION.COPY)
$(ISOROOT)/nailgun/solo/%: iso/solo/% ; $(ACTION.COPY)
$(ISOROOT)/nailgun/bin/%: bin/% ; $(ACTION.COPY)
$(ISOROOT)/nailgun/%: nailgun/% ; $(ACTION.COPY)
$(ISOROOT)/eggs:
	mkdir -p $@
$(ISOROOT)/eggs/%: $(LOCAL_MIRROR)/eggs/% ; $(ACTION.COPY)


$(ISOROOT)/gems/gems:
	mkdir -p $@

$(ISOROOT)/gems/gems/%: $(LOCAL_MIRROR)/gems/% | $(ISOROOT)/gems/gems
	echo $@
	$(ACTION.COPY)

$/isoroot-gems.done: $(addprefix $(ISOROOT)/gems/gems/,$(call find-files,$(LOCAL_MIRROR)/gems))
	gem generate_index -d $(ISOROOT)/gems
	$(ACTION.TOUCH)

# MAIN ISO RULE

$/nailgun-ubuntu-12.04-amd64.iso: $/isoroot.done $(ISOROOT)/md5sum.txt
	rm -f $@
	mkisofs -r -V "Mirantis Nailgun" \
		-cache-inodes \
		-J -l -b isolinux/isolinux.bin \
		-c isolinux/boot.cat -no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-o $@ $(ISOROOT)

endif

