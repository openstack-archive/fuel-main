
/:=$(BUILD_DIR)/packages/ubuntu/

$/%: /:=$/

APT-GET:=apt-get

EXTRA_PACKAGES:=$(shell grep -v ^\\s*\# requirements-deb.txt)

UBUNTU_MIRROR:=http://ru.archive.ubuntu.com/ubuntu
OPSCODE_UBUNTU_MIRROR:=http://apt.opscode.com
# DEBIAN PACKET CACHE RULES

define apt_conf_contents
APT
{
  Architecture "amd64";
  Default-Release "$(UBUNTU_1204_RELEASE)";
  Get::AllowUnauthenticated "true";
};

Dir
{
  State "$(abspath $/state)";
  State::status "status";
  Cache::archives "$(abspath $/archives)";
  Cache "$(abspath $/cache)";
  Etc "$(abspath $/etc)";
};
endef

$/etc/apt.conf: export contents:=$(apt_conf_contents)
$/etc/apt.conf: | $/etc/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


define apt_sources_list_contents
deb $(UBUNTU_MIRROR) precise main restricted universe multiverse
deb-src $(UBUNTU_MIRROR) precise main restricted universe multiverse
deb $(OPSCODE_UBUNTU_MIRROR) $(UBUNTU_1204_RELEASE)-0.10 main
endef

$/etc/sources.list: export contents:=$(apt_sources_list_contents)
$/etc/sources.list: | $/etc/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


define opscode_preferences_contents
Package: *
Pin: origin "apt.opscode.com"
Pin-Priority: 999
endef

$/etc/preferences.d/opscode: export contents:=$(opscode_preferences_contents)
$/etc/preferences.d/opscode: | $/etc/preferences.d/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@


$/state/status: | $/state/.dir
	$(ACTION.TOUCH)

$/cache-infra.done: \
	  $/etc/apt.conf \
		$/etc/sources.list \
		$/etc/preferences.d/opscode \
	  $/archives/.dir \
		| $/cache/.dir \
		  $/state/status
	$(ACTION.TOUCH)

$/cache-iso.done: $(UBUNTU_1204_ISO) | $(UBUNTU_1204_ROOT)/pool $/archives/.dir
	find $(abspath $(UBUNTU_1204_ROOT)/pool) -type f \( -name '*.deb' -o -name '*.udeb' \) -exec ln -sf {} $/archives \;
	$(ACTION.TOUCH)

$/cache-index.done: \
	  $/cache-infra.done \
	  $(addprefix $/state/,$(call find-files,$(BINARIES_DIR)/ubuntu/precise/state))
	$(APT-GET) -c=$/etc/apt.conf update
	$(ACTION.TOUCH)

$/cache-extra.done: \
	  $/cache-index.done \
		$/cache-iso.done \
		$(addprefix $/archives/,$(call find-files,$(BINARIES_DIR)/ubuntu/$(UBUNTU_1204_RELEASE)/extra)) \
		requirements-deb.txt
	for p in $(EXTRA_PACKAGES); do \
	  $(APT-GET) -c=$/etc/apt.conf -d -y install $$p; \
	done
	$(ACTION.TOUCH)

$/archives/%.deb: $(BINARIES_DIR)/ubuntu/$(UBUNTU_1204_RELEASE)/extra/%.deb
	ln -sf $(abspath $<) $@

$/cache.done: $/cache-extra.done
	$(ACTION.TOUCH)






