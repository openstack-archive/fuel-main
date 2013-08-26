include $(SOURCE_DIR)/mirror/rhel/yum_repos.mk

.PHONY: show-yum-urls-rhel

$(BUILD_DIR)/mirror/rhel/etc/yum.conf: $(call depv,rhel_yum_conf)
$(BUILD_DIR)/mirror/rhel/etc/yum.conf: export contents:=$(rhel_yum_conf)
$(BUILD_DIR)/mirror/rhel/etc/yum.conf:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/mirror/rhel/etc/yum-plugins/priorities.py: \
		$(SOURCE_DIR)/mirror/rhel/yum-priorities-plugin.py
	mkdir -p $(@D)
	cp $(SOURCE_DIR)/mirror/rhel/yum-priorities-plugin.py $@

$(BUILD_DIR)/mirror/rhel/etc/yum/pluginconf.d/priorities.conf:
	mkdir -p $(@D)
	/bin/echo -e "[main]\nenabled=1\ncheck_obsoletes=1\nfull_match=1" > $@

$(BUILD_DIR)/mirror/rhel/etc/yum.repos.d/base.repo: $(call depv,YUM_REPOS)
$(BUILD_DIR)/mirror/rhel/etc/yum.repos.d/base.repo: \
		export contents:=$(foreach repo,$(YUM_REPOS),\n$(rhel_yum_repo_$(repo))\n)
$(BUILD_DIR)/mirror/rhel/etc/yum.repos.d/base.repo:
	@mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/mirror/rhel/yum-config.done: \
		$(BUILD_DIR)/mirror/rhel/etc/yum.conf \
		$(BUILD_DIR)/mirror/rhel/etc/yum.repos.d/base.repo \
		$(BUILD_DIR)/mirror/rhel/etc/yum-plugins/priorities.py \
		$(BUILD_DIR)/mirror/rhel/etc/yum/pluginconf.d/priorities.conf
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/rhel/yum.done: $(call depv,REQ_RHEL_RPMS)
$(BUILD_DIR)/mirror/rhel/yum.done: \
		$(BUILD_DIR)/mirror/rhel/yum-config.done
	yum -c $(BUILD_DIR)/mirror/rhel/etc/yum.conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
	yumdownloader -q --resolve --archlist=$(CENTOS_ARCH) \
		-c $(BUILD_DIR)/mirror/rhel/etc/yum.conf \
		--destdir=$(LOCAL_MIRROR_RHEL)/Packages \
		`echo $(REQ_RHEL_RPMS) | /bin/sed 's/-[0-9][0-9\.a-zA-Z_-]\+//g'`
	$(ACTION.TOUCH)

show-yum-urls-rhel: $(call depv,REQ_RHEL_RPMS)
show-yum-urls-rhel: \
		$(BUILD_DIR)/mirror/rhel/yum-config.done
	yum -c $(BUILD_DIR)/mirror/rhel/etc/yum.conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
	yumdownloader --urls -q --resolve --archlist=$(CENTOS_ARCH) \
		-c $(BUILD_DIR)/mirror/rhel/etc/yum.conf \
		--destdir=$(LOCAL_MIRROR_RHEL)/Packages \
		`echo $(REQ_RHEL_RPMS) | /bin/sed 's/-[0-9][0-9\.a-zA-Z_-]\+//g'`

$(LOCAL_MIRROR_RHEL)/comps.xml: \
		export COMPSXML=$(shell wget -qO- $(MIRROR_RHEL)/repodata/repomd.xml | grep -m 1 '$(@F)' | awk -F'"' '{ print $$2 }')
$(LOCAL_MIRROR_RHEL)/comps.xml:
	@mkdir -p $(@D)
	if ( echo $${COMPSXML} | grep -q '\.gz$$' ); then \
		wget -O $@.gz $(MIRROR_RHEL)/$${COMPSXML}; \
		gunzip $@.gz; \
	else \
		wget -O $@ $(MIRROR_RHEL)/$${COMPSXML}; \
	fi

# These packages are used by FUEL but RHEL repo doesn't contain them. So we
# need to download them from some external repo and put into rhel/fuel repo.
HACK_PACKAGES:=xinetd-2.3.14-38.el6.x86_64.rpm xfsprogs-3.1.1-10.el6.x86_64.rpm qpid-cpp-server-cluster-0.14-22.el6_3.x86_64.rpm \
qpid-cpp-server-store-0.14-22.el6_3.x86_64.rpm qpid-tests-0.14-1.el6_2.noarch.rpm qpid-tools-0.14-6.el6_3.noarch.rpm \
qpid-cpp-server-ssl-0.14-22.el6_3.x86_64.rpm
HACK_URLS:=$(addprefix http://mirror.yandex.ru/centos/6.4/os/x86_64/Packages/,$(HACK_PACKAGES))

$(BUILD_DIR)/mirror/rhel/fuel.done:
	mkdir -p $(LOCAL_MIRROR)/mirror/rhel/fuel/Packages
	-wget -c -i $(SOURCE_DIR)/puppet/rpmcache/files/req-fuel-rhel.txt -B http://download.mirantis.com/epel-fuel-grizzly/x86_64/ -P $(LOCAL_MIRROR)/rhel/fuel/Packages
	-wget -c -i $(SOURCE_DIR)/puppet/rpmcache/files/req-fuel-rhel.txt -B http://download.mirantis.com/epel-fuel-grizzly/noarch/ -P $(LOCAL_MIRROR)/rhel/fuel/Packages
	-wget -c -i $(SOURCE_DIR)/puppet/rpmcache/files/req-fuel-rhel.txt -B http://srv11-msk.msk.mirantis.net/rhel6/fuel-rpms/x86_64/ -P $(LOCAL_MIRROR)/rhel/fuel/Packages
	-wget -c -P $(LOCAL_MIRROR)/rhel/fuel/Packages $(HACK_URLS)
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/rhel/repo.done: \
		$(BUILD_DIR)/mirror/rhel/yum.done \
		$(BUILD_DIR)/mirror/rhel/fuel.done \
		| $(LOCAL_MIRROR_RHEL)/comps.xml
	createrepo -g $(LOCAL_MIRROR_RHEL)/comps.xml \
		-o $(LOCAL_MIRROR_RHEL)/ $(LOCAL_MIRROR_RHEL)/
	$(ACTION.TOUCH)
