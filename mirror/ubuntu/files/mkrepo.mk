#!/usr/bin/make -f

requirements_deb:=$(shell cat /requirements-deb.txt)

downloads_list:=/repo/download/download_urls.list
deb_download_stamp:=/tmp/deb-downloads.stamp
pkg_downloads_lst:=$(requirements_deb:%=/tmp/downloads_%.list)

# Note: apt-get install --print-uris package
# is not going to print anything if the package is already installed. Thus
# the base packages will be omitted if we use the main APT/dpkg settings.
# Pretend that no package has been installed by creating an alternative APT
# state and configuration directories.

apt_altstate:=/tmp/apt-altstate
apt_lists_dir:=$(apt_altstate)/var/lib/apt/lists
apt_cache_dir:=$(apt_altstate)/var/cache/apt
null_dpkg_status:=$(apt_altstate)/var/lib/dpkg/status
apt_setup_stamp:=/tmp/apt-altstate-setup.stamp

apt_altstate_opts:=\
	-o APT::Get::AllowUnauthenticated=1 \
	-o Dir::State::Lists=$(apt_lists_dir) \
	-o Dir::State::status=$(null_dpkg_status) \
	-o Dir::Cache=$(apt_cache_dir)

all: $(deb_download_stamp)

deb_download: $(deb_download_stamp)

downloads_list: $(downloads_list)

$(downloads_list): $(pkg_downloads_lst)
	mkdir -p $(dir $@)
	cat $^ > $@.tmp.all
	sed -rne "s/^'([^']+)['].*$$/\1/p" -i $@.tmp.all
	sort -u < $@.tmp.all > $@.tmp
	mv $@.tmp $@

$(null_dpkg_status):
	mkdir -p "$(apt_altstate)" && \
	mkdir -p "$(apt_lists_dir)" && \
	mkdir -p "$(apt_cache_dir)" && \
	mkdir -p "$(dir $(null_dpkg_status))" && \
	touch $@

$(apt_setup_stamp): $(null_dpkg_status)
	apt-get $(apt_altstate_opts) update
	touch $@

$(pkg_downloads_lst): /tmp/downloads_%.list: $(apt_setup_stamp)
	apt_log=$(dir $@)/apt_$*.log; \
	if ! apt-get $(apt_altstate_opts) --print-uris --yes -qq install $* >$@.tmp 2>"$${apt_log}"; then \
		echo "package $* can not be installed" >> "$${apt_log}"; \
		apt-get -o Debug::pkgProblemResolver=true $(apt_altstate_opts) --print-uris --yes install $* >>"$${apt_log}" 2>&1; \
		exit 1; \
	fi; \
	mv $@.tmp $@

$(deb_download_stamp): $(downloads_list)
	xargs -n1 -P4 wget -nv -P "$(dir $<)" < $< || exit 1
	touch $@
