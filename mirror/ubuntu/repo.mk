#!/usr/bin/make -f

# the root APT repo metadata:
repo_release_file:=$(LOCAL_MIRROR_UBUNTU)/dists/$(UBUNTU_RELEASE)/Release

all: $(repo_release_file)

workdir?=$(BUILD_DIR)/mirror/ubuntu
target_dir?=$(LOCAL_MIRROR_UBUNTU)/pool/main
udeb_target_dir?=$(LOCAL_MIRROR_UBUNTU)/pool/debian-installer
indices_dir?=$(LOCAL_MIRROR_UBUNTU)/indices

deb_download_urls:=$(workdir)/deb_download_urls.list
udeb_download_urls:=$(workdir)/udeb_download_urls.list
udebs_list:=$(workdir)/udebs.list
deb_download_done:=$(workdir)/deb_download.done
udeb_download_done:=$(workdir)/udeb_download.done

deb_download: $(deb_download_done)
deb_download_urls: $(deb_download_urls)

# The version of some packages might contain an epoch, which is separated by
# a semicolon, which is a bit special for make. Therefore replace semicolons
# with a special sequence
decode_versions=$(subst ___,:,$(1))
# Replace a special sequence denoting the semicolon with the semicolon character
encode_versions=$(subst :,___,$(1))

requirements_deb:=$(call encode_versions,$(shell cat $(SOURCE_DIR)/requirements-deb.txt))
include $(BUILD_DIR)/ubuntu_installer_kernel_version.mk
kernel_pkgs:=\
linux-image-generic-$(UBUNTU_KERNEL_FLAVOR) \
linux-headers-generic-$(UBUNTU_KERNEL_FLAVOR) \
linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION) \
linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION)
requirements_deb+=$(kernel_pkgs)

include $(workdir)/conflicting_pkgs_list.mk

per_pkg_downloads_urls:=$(conflicting_pkgs:%=$(workdir)/urllists/%.list)
$(info per_pkg_downloads_urls=$(per_pkg_downloads_urls))

# Setup a separate APT/dpkg databases to not interfere with the system one.
# Note: apt-get install --print-uris package
# is not going to print anything if the package is already installed. Thus
# the base packages will be omitted if we use the main APT/dpkg settings.
# Pretend that no package has been installed by creating an alternative APT
# state and configuration directories.

define newline


endef

define apt_sources_list
$(if $(subst none,,$(USE_MIRROR)),
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main main/debian-installer,

# USE_MIRROR=none
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main universe multiverse restricted
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-updates main universe multiverse restricted
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-security main universe multiverse restricted
deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main
deb $(MIRROR_UBUNTU_SECURITY) $(UBUNTU_RELEASE)-security main universe multiverse restricted
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE) main/debian-installer universe/debian-installer multiverse/debian-installer restricted/debian-installer
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-updates main/debian-installer universe/debian-installer multiverse/debian-installer restricted/debian-installer
deb $(MIRROR_UBUNTU) $(UBUNTU_RELEASE)-security main/debian-installer universe/debian-installer multiverse/debian-installer restricted/debian-installer
deb $(MIRROR_FUEL_UBUNTU) $(UBUNTU_RELEASE) main/debian-installer
deb $(MIRROR_UBUNTU_SECURITY) $(UBUNTU_RELEASE)-security main/debian-installer universe/debian-installer multiverse/debian-installer restricted/debian-installer
)
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb ,deb $(EXTRA_DEB_REPOS)))
endef

apt_altstate:=$(workdir)/apt-altstate
apt_alt_conf:=$(apt_altstate)/etc/apt/apt.conf

define apt_config
Dir::Etc::SourceList "$(apt_altstate)/etc/apt/sources.list";
Dir::Etc::SourceParts "$(apt_altstate)/etc/apt/sources.list.d";
Dir::Etc::Preferences "$(apt_altstate)/etc/apt/preferences";
Dir::Etc::PreferencesParts "$(apt_altstate)/etc/apt/preferences.d";
Dir::State::Lists "$(apt_altstate)/var/lib/apt/lists";
Dir::State::Status "$(apt_altstate)/var/lib/dpkg/status";
Dir::Cache "$(apt_altstate)/var/cache/apt";
APT::Install-Recommends "1";
APT::Get::AllowUnauthenticated "true";
$(if $(strip $(HTTP_PROXY)),
Acquire::http::Proxy "$(strip $(HTTP_PROXY))";)
endef

apt_setup_done:=$(workdir)/apt_setup.done

$(apt_setup_done): export apt_conf:=$(apt_config)
$(apt_setup_done): export sources_lists:=$(apt_sources_list)
$(apt_setup_done):
	rm -rf "$(apt_altstate)" && \
	mkdir -p "$(apt_altstate)/etc/apt/sources.list.d" && \
	mkdir -p "$(apt_altstate)/etc/apt/preferences.d" && \
	mkdir -p "$(apt_altstate)/var/lib/apt/lists" && \
	mkdir -p "$(apt_altstate)/var/cache/apt/archives/partial" && \
	mkdir -p "$(apt_altstate)/var/lib/dpkg" && \
	touch "$(apt_altstate)/var/lib/dpkg/status" && \
	echo "$$apt_conf" > "$(apt_altstate)/etc/apt/apt.conf" && \
	echo "$$sources_lists" > "$(apt_altstate)/etc/apt/sources.list" && \
	cp $(SOURCE_DIR)/mirror/ubuntu/files/preferences "$(apt_altstate)/etc/apt" && \
	mkdir -p "$(workdir)/urllists" "$(workdir)/log" && \
	apt-get -c "$(apt_alt_conf)" update && \
	touch $@

$(apt_altstate)/var/lib/dpkg/available: $(apt_setup_done)
	apt-cache -c "$(apt_alt_conf)" dumpavail > "$@.tmp" && \
	mv "$@.tmp" "$@"

nonconflicting_urls_list:=$(workdir)/deb_download_noconflicts_urls.list
# Some packages (like nova-compute-kvm and nova-compute-qemu) conflict
# with each other, but we still need all of them in the mirror
conflicting_pkgs_list:=$(workdir)/conflicting_pkgs.list
rest_pkgs_list:=$(workdir)/rest_pkgs.list

$(workdir)/requirements-deb.txt: $(SOURCE_DIR)/requirements-deb.txt
	mkdir -p "$(dir $@)" && \
	cp $< $@.pre && \
	echo '$(kernel_pkgs)' >> $@.pre && \
	sort -u < $@.pre > $@.tmp && \
	mv $@.tmp $@

# Figure out which packages conflict each others. Try to install all
# packages, and grep the APT log for Conflicts.
# XXX: sometimes apt reports conflicts as missing dependencies
# mysql-server-wsrep-5.6 : Depends: mysql-client-5.6 (>= 5.6.16-2~mos6.1+1) but it is not going to be installed
# The actual issue is that mysql-client-5.6 conflicts with mysql-client
# However some dependencies might be actually broken, therefore we make
# a few attempts and fall back to processing packages one by one
$(nonconflicting_urls_list): $(workdir)/requirements-deb.txt $(apt_setup_done)
	max_attempts=10; \
	count=0; \
	cp $< '$(rest_pkgs_list).tmp' && \
	touch '$(conflicting_pkgs_list).tmp' && \
	broken='' && \
	while [ $$count -lt $$max_attempts ]; do \
		apt_out="$(workdir)/apt_$${count}.out"; \
		apt_log="$(workdir)/apt_$${count}.log"; \
		more_conflicting_pkgs="$(workdir)/more_conflicting_pkgs.list"; \
		if ! apt-get -c "$(apt_alt_conf)" --print-uris --yes -q install `cat $(rest_pkgs_list).tmp` >"$$apt_out" 2>"$$apt_log"; then \
			broken='yes' && \
			sed -rne 's/^\s*([^: ]+)\s*:\s*(Conflicts|Depends):.*$$/\1/p' < "$$apt_out" > "$$more_conflicting_pkgs" && \
			cat "$$more_conflicting_pkgs" '$(conflicting_pkgs_list).tmp' | \
				sort -u > '$(conflicting_pkgs_list).tmp.new' && \
			mv '$(conflicting_pkgs_list).tmp.new' '$(conflicting_pkgs_list).tmp' && \
			comm -23 '$(rest_pkgs_list).tmp' '$(conflicting_pkgs_list).tmp' > '$(rest_pkgs_list).tmp.new' && \
			sort -u < '$(rest_pkgs_list).tmp.new' > '$(rest_pkgs_list).tmp'; \
		else \
			broken=''; \
			mv "$$apt_out" "$@.tmp" && \
			break; \
		fi; \
		count=$$((count+1)); \
	done; \
	if [ -z "$$broken" ]; then \
		mv "$(conflicting_pkgs_list).tmp" "$(conflicting_pkgs_list)" && \
		mv "$@.tmp" "$@"; \
	else \
		cp "$(SOURCE_DIR)/requirements_deb.txt" "$(conflicting_pkgs_list)" && \
		echo '$(extra_deb_pkgs)' >> "$(conflicting_pkgs_list)" && \
		touch "$@"; \
	fi

$(conflicting_pkgs_list): $(nonconflicting_urls_list)

$(workdir)/conflicting_pkgs_list.mk: $(conflicting_pkgs_list)
	echo 'conflicting_pkgs:=\\' > $@.tmp && \
	sed -e 's/$$/\\/' -e 's/:/___/g' < $< >> $@.tmp && \
	echo '$$(empty)' >> $@.tmp && \
	mv $@.tmp $@

# Get the download URLs for each package in requirements-deb.txt.
# This takes into account package dependencies. Note that downloading
# all packages at once is not possible due to the conflicts.
$(per_pkg_downloads_urls): $(workdir)/urllists/%.list: $(apt_setup_done)
	apt_log="$(workdir)/log/$*.log"; \
	pkg="$(call decode_versions,$*)"; \
	if ! apt-get -c "$(apt_alt_conf)" --print-uris --yes -qq install "$$pkg" >"$@.tmp" 2>"$${apt_log}"; then \
		echo "package $* can not be installed" >> "$${apt_log}"; \
		apt-get -c "$(apt_alt_conf)" -o Debug::pkgProblemResolver=true  --print-uris --yes install "$$pkg" >>"$${apt_log}" 2>&1; \
		exit 1; \
	fi; \
	mv $@.tmp $@

# Declaring dependency on an Essential package is not mandatory,
# hence we need to make sure the essential packages are mirrored too.
# XXX: dpkg-query works with dpkg database (and we have it empty on purpose)
# Also dpkg-query --load-avail produces wrong result, hence sed hackery
$(workdir)/essential_pkgs.list: $(apt_altstate)/var/lib/dpkg/available
	sed -rne '/^Package/ h; /^Essential:\s+yes$$/ { g; s/^Package:\s+(.+)$$/\1/p; d }' < $< > $@.unsorted
	sort -u < $@.unsorted > $@.tmp && \
	mv $@.tmp $@

essential_pkgs_urls:=$(workdir)/urllists/essential_pkgs.list
# XXX: take a shortcut for essential packages: just ask apt to download them
# (or rather print their URL). An essential package can only depend on other
# essential packages, therefore dependency calculation can be skipped
$(essential_pkgs_urls): $(workdir)/essential_pkgs.list
	apt_log="$(workdir)/log/essential_pkgs.log"; \
	if ! apt-get -c "$(apt_alt_conf)" download -qq --print-uris `cat $<` > $@.tmp 2>"$$apt_log"; then \
		echo 'Essential packages can not be installed' >>"$$apt_log"; \
		exit 1; \
	fi; \
	mv $@.tmp $@


# udebs are required for the provisioning with cobbler + Debian installer
# Download almost all udebs, skip the modules for the kernels different 
# from that used by the installer (to save *a lot* of disk space).
$(udeb_download_urls): $(workdir)/udeb_pkgs_filtered.list
	apt_log="$(workdir)/log/udeb_pkgs.log"; \
	if ! apt-get -c "$(apt_alt_conf)" download -qq --print-uris `cat $<` > $@.unsorted 2>"$$apt_log"; then \
		echo 'Udebs can not be downloaded' >>"$$apt_log"; \
		apt-get -c "$(apt_alt_conf)" download -o Debug::pkgProblemResolver=yes `cat $<` >>"$$apt_log" 2>&1; \
		exit 1; \
	fi
	sed -rne "s/^'([^']+)['].*$$/\1/p" -i $@.unsorted && \
	sort -u < $@.unsorted > $@.tmp && \
	mv $@.tmp $@

# udebs are in Section: debian-installer or {universe,multiverse}/debian-installer
$(workdir)/udeb_pkgs.list: $(apt_altstate)/var/lib/dpkg/available
	sed -rne '/^Package/h; /^Section:\s+.*debian-installer/ { g; s/Package:\s+(.+)$$/\1/p }' < $< > $@.unsorted
	sort -u < $@.unsorted > $@.tmp && \
	mv $@.tmp $@

# Skip kernel modules udebs for kernels other than the one used by the installer
$(workdir)/udeb_pkgs_filtered.list: $(workdir)/udeb_pkgs.list
	sed -re '/^(.+-modules-.*|kernel-image|kernel-signed-image).*-generic-di$$/ { s/$(UBUNTU_INSTALLER_KERNEL_VERSION)/&/p; d; }' < $< > $@.unsorted && \
	sort -u < $@.unsorted > $@.tmp && \
	mv $@.tmp $@


$(deb_download_urls): $(nonconflicting_urls_list) $(per_pkg_downloads_urls) $(essential_pkgs_urls)
	mkdir -p "$(dir $@)" && \
	cat $^ > $@.tmp.all && \
	sed -rne "s/^'([^']+)['].*$$/\1/p" -i $@.tmp.all && \
	sort -u < $@.tmp.all > $@.tmp && \
	mv $@.tmp $@

$(deb_download_done): $(deb_download_urls)
	mkdir -p "$(target_dir)" && \
	xargs -n1 -P4 wget -nv -P "$(target_dir)" < $< || exit 1
	touch $@

$(udeb_download_done): $(udeb_download_urls)
	mkdir -p "$(udeb_target_dir)" && \
	xargs -n1 -P4 wget -nv -P "$(udeb_target_dir)" < $< || exit 1
	touch $@


combined_overrides:=$(LOCAL_MIRROR_UBUNTU)/indices/override.$(UBUNTU_RELEASE).main
combined_extra_overrides:=$(LOCAL_MIRROR_UBUNTU)/indices/override.$(UBUNTU_RELEASE).extra.main
combined_di_overrides:=$(LOCAL_MIRROR_UBUNTU)/indices/override.$(UBUNTU_RELEASE).main.debian-installer

define apt_ftparchive_conf
Dir {
	ArchiveDir "$(LOCAL_MIRROR_UBUNTU)";
};
TreeDefault {
	Directory "pool";
}
BinDirectory "pool/main" {
	Packages "dists/$(UBUNTU_RELEASE)/main/binary-$(UBUNTU_ARCH)/Packages";
	BinOverride "$(combined_overrides)";
	ExtraOverride "$(combined_extra_overrides)";
};
BinDirectory "pool/debian-installer" {
	Packages "dists/$(UBUNTU_RELEASE)/main/debian-installer/binary-$(UBUNTU_ARCH)/Packages";
	BinOverride "$(combined_di_overrides)";
};
Default {
	Packages::Extensions ".deb .udeb";
	Packages::Compress ". gzip";
	Contents::Compress "gzip";
};
Contents {
	Compress "gzip";
};
endef

apt_repo_components:=main main/debian-installer

define apt_ftparchive_release_conf
APT::FTPArchive::Release::Origin "Ubuntu";
APT::FTPArchive::Release::Label "Ubuntu";
APT::FTPArchive::Release::Suite "$(UBUNTU_RELEASE)";
APT::FTPArchive::Release::Version "$(UBUNTU_RELEASE_NUMBER)";
APT::FTPArchive::Release::Codename "$(UBUNTU_RELEASE)";
APT::FTPArchive::Release::Architectures "$(UBUNTU_ARCH)";
APT::FTPArchive::Release::Components "main";
APT::FTPArchive::Release::Description "Ubuntu $(UBUNTU_RELEASE) $(UBUNTU_RELEASE_NUMBER) LTS";
endef

define component_release
Archive: $(UBUNTU_RELEASE)
Version: $(UBUNTU_RELEASE_NUMBER)
Component: main
Origin: Ubuntu
Label: Ubuntu
Architecture: $(UBUNTU_ARCH)
endef

$(repo_release_file): export APT_FTPARCHIVE_CONF:=$(apt_ftparchive_conf)
$(repo_release_file): export APT_FTPARCHIVE_RELEASE_CONF:=$(apt_ftparchive_release_conf)
$(repo_release_file): export COMPONENT_RELEASE:=$(component_release)
$(repo_release_file): $(deb_download_done) $(udeb_download_done)
	mkdir -p "$(workdir)/conf" && \
	echo "$$APT_FTPARCHIVE_CONF" > "$(workdir)/conf/apt-ftparchive.conf" && \
	echo "$$APT_FTPARCHIVE_RELEASE_CONF" > "$(workdir)/conf/apt-ftparchive-release.conf"
	for component in $(apt_repo_components); do \
		dists_dir="$(dir $@)$$component/binary-$(UBUNTU_ARCH)"; \
		rm -rf "$$dists_dir"; \
		mkdir -p "$$dists_dir" && \
		echo "$$COMPONENT_RELEASE" > "$$dists_dir/Release"; \
	done
	apt-ftparchive -c "$(workdir)/conf/apt-ftparchive-release.conf" generate "$(workdir)/conf/apt-ftparchive.conf"
### XXX: The Packages file produced by apt-ftparchive generate is not sorted properly.
### XXX: Sort them manually to prevent the provisioning error.
	for component in $(apt_repo_components); do \
		pkgs_file="$(dir $@)$$component/binary-$(UBUNTU_ARCH)/Packages"; \
		rm -f "$${pkgs_file}.gz" && \
		apt-sortpkgs "$$pkgs_file" > "$${pkgs_file}.new" && \
		gzip -c < "$${pkgs_file}.new" > "$${pkgs_file}.gz.new" && \
		mv "$${pkgs_file}.new" "$${pkgs_file}" && \
		mv "$${pkgs_file}.gz.new" "$${pkgs_file}.gz"; \
	done
### XXX: Ubuntu configures dpkg to use both amd64 and i386 packages. Thus
### XXX: apt-get update expects to find binary-i386/{Packages,Release} files
### XXX: and fails if these are absent. Therefore one need to simulate
### XXX: a biarch APT repo even if there are no actual i386 packages.
ifeq (amd64,$(UBUNTU_ARCH))
	for component in $(apt_repo_components); do \
		bdir="$(dir $@)$$component/binary-i386"; \
		rm -rf "$$bdir" && \
		mkdir -p "$$bdir" && \
		touch "$$bdir/Packages" && \
		echo "$$APT_FTPARCHIVE_RELEASE_CONF" | sed -e 's/$(UBUNTU_ARCH)/i386/g' > "$$bdir/Release"; \
	done
endif
	apt-ftparchive -c "$(workdir)/conf/apt-ftparchive-release.conf" release "$(dir $@)" > "$@.tmp"
	mv "$@.tmp" "$@"

$(repo_release_file): $(combined_overrides) \
	$(combined_extra_overrides) \
	$(combined_di_overrides)

ifeq (none,$(strip $(USE_MIRROR)))
overrides:=\
override.$(UBUNTU_RELEASE).main \
override.$(UBUNTU_RELEASE).restricted \
override.$(UBUNTU_RELEASE).universe \
override.$(UBUNTU_RELEASE).multiverse \
override.$(UBUNTU_RELEASE)-updates.main \
override.$(UBUNTU_RELEASE)-updates.restricted \
override.$(UBUNTU_RELEASE)-updates.universe \
override.$(UBUNTU_RELEASE)-updates.multiverse \
override.$(UBUNTU_RELEASE)-security.main \
override.$(UBUNTU_RELEASE)-security.restricted \
override.$(UBUNTU_RELEASE)-security.universe \
override.$(UBUNTU_RELEASE)-security.multiverse \
$(empty)

extra_overrides:=\
override.$(UBUNTU_RELEASE).extra.main \
override.$(UBUNTU_RELEASE).extra.restricted \
override.$(UBUNTU_RELEASE).extra.universe \
override.$(UBUNTU_RELEASE).extra.multiverse \
override.$(UBUNTU_RELEASE)-updates.extra.main \
override.$(UBUNTU_RELEASE)-updates.extra.restricted \
override.$(UBUNTU_RELEASE)-updates.extra.universe \
override.$(UBUNTU_RELEASE)-updates.extra.multiverse \
override.$(UBUNTU_RELEASE)-security.extra.main \
override.$(UBUNTU_RELEASE)-security.extra.restricted \
override.$(UBUNTU_RELEASE)-security.extra.universe \
override.$(UBUNTU_RELEASE)-security.extra.multiverse \
$(empty)

di_overrides:=\
override.$(UBUNTU_RELEASE).main.debian-installer \
override.$(UBUNTU_RELEASE).restricted.debian-installer \
override.$(UBUNTU_RELEASE).universe.debian-installer \
override.$(UBUNTU_RELEASE).multiverse.debian-installer \
override.$(UBUNTU_RELEASE)-updates.main.debian-installer \
override.$(UBUNTU_RELEASE)-updates.restricted.debian-installer \
override.$(UBUNTU_RELEASE)-updates.universe.debian-installer \
override.$(UBUNTU_RELEASE)-updates.multiverse.debian-installer \
override.$(UBUNTU_RELEASE)-security.main.debian-installer \
override.$(UBUNTU_RELEASE)-security.restricted.debian-installer \
override.$(UBUNTU_RELEASE)-security.universe.debian-installer \
override.$(UBUNTU_RELEASE)-security.multiverse.debian-installer \
$(empty)

overrides_dl:=$(foreach idx,$(overrides) $(extra_overrides) $(di_overrides),$(workdir)/indices/$(idx))

$(overrides_dl): $(workdir)/indices/%:
	mkdir -p "$(dir $@)" && \
	rm -f "$@.tmp" && \
	wget -nv -O "$@.tmp" "$(MIRROR_UBUNTU)/indices/$*" && \
	mv "$@.tmp" "$@"

$(combined_overrides): $(overrides:%=$(workdir)/indices/%)
	mkdir -p "$(dir $@)" && \
	cat $^ > "$@.unsorted" && \
	sed -re '/Supported/d' -i "$@.unsorted" && \
	sort -u < "$@.unsorted" > "$@.tmp" && \
	mv "$@.tmp" "$@"

$(combined_extra_overrides): $(extra_overrides:%=$(workdir)/indices/%)
	mkdir -p "$(dir $@)" && \
	cat $^ > "$@.unsorted" && \
	sed -re '/Supported/d' -i "$@.unsorted" && \
	sort -u < "$@.unsorted" > "$@.tmp" && \
	mv "$@.tmp" "$@"

$(combined_di_overrides): $(di_overrides:%=$(workdir)/indices/%)
	mkdir -p "$(dir $@)" && \
	cat $^ > "$@.unsorted" && \
	sed -re '/Supported/d' -i "$@.unsorted" && \
	sort -u < "$@.unsorted" > "$@.tmp" && \
	mv "$@.tmp" "$@"

else
overrides_dl:=$(combined_overrides) $(combined_extra_overrides) $(combined_di_overrides)

$(overrides_dl): $(LOCAL_MIRROR_UBUNTU)/indices/%:
	mkdir -p "$(dir $@)" && \
	rm -f "$@.tmp" && \
	wget -nv -O "$@.tmp" "$(MIRROR_UBUNTU)/indices/$*" && \
	mv $@.tmp $@
endif
