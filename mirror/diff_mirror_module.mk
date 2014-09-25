.PHONY: mirror_diff diff-mirror

mirror_diff: $(BUILD_DIR)/mirror/mirror_diff.done

$(BUILD_DIR)/mirror/mirror_diff.done: \
	$(BUILD_DIR)/mirror/build.done

	mkdir -p $(DIFF_MIRROR_CENTOS_OS_PKGS)
	mkdir -p $(DIFF_MIRROR_UBUNTU_OS_PKGS)

	# NOTE: please, be sure that the folders definition have the below syntax
	# rsync -avrqSHP --compare-dest=/folder_old /folder_new/ /folder_result
	# otherwise rsync result will be completly wrong
	# centos
	rsync -avqSHP --checksum --delete --compare-dest=/tmp/mirrors/5.1.1/centos/os/x86_64/Packages \
    $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages/ \
    $(DIFF_MIRROR_CENTOS_OS_PKGS)
  # ubuntu
	rsync -avqSHP --checksum --delete --compare-dest=/tmp/mirrors/5.1.1/ubuntu/pool/main \
    $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main/ \
    $(DIFF_MIRROR_UBUNTU_OS_PKGS)

  # create centos repo
	createrepo $(DIFF_MIRROR_CENTOS_OS_PKGS) -o $(DIFF_MIRROR_CENTOS_OS_PKGS)/../
	# create ubuntu repo
	dpkg-scanpackages -m $(DIFF_MIRROR_UBUNTU_OS_PKGS) > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages
	gzip -9c $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages.gz

	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/mirror_diff2.done: \
	$(BUILD_DIR)/mirror/build.done

	mkdir -p $(DIFF_MIRROR_CENTOS_OS_PKGS)
	mkdir -p $(DIFF_MIRROR_UBUNTU_OS_PKGS)

	# centos
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh \
		$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages/ \
		/tmp/mirrors/5.1.1/centos/os/x86_64/Packages \
		$(DIFF_MIRROR_CENTOS_OS_PKGS)
	# ubuntu
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh \
		$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main/ \
		/tmp/mirrors/5.1.1/ubuntu/pool/main \
		$(DIFF_MIRROR_UBUNTU_OS_PKGS)

  # create centos repo
	createrepo $(DIFF_MIRROR_CENTOS_OS_PKGS) -o $(DIFF_MIRROR_CENTOS_OS_PKGS)/../
	# create ubuntu repo
	dpkg-scanpackages -m $(DIFF_MIRROR_UBUNTU_OS_PKGS) > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages
	gzip -9c $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages.gz

	$(ACTION.TOUCH)

########################
# DIFF_MIRROR ARTIFACT
########################
diff-mirror: $(ARTS_DIR)/$(DIFF_MIRROR_ART_NAME)

$(ARTS_DIR)/$(DIFF_MIRROR_ART_NAME): $(BUILD_DIR)/iso/mirror-diff.done
	mkdir -p $(@D)
	tar cf $@ -C $(LOCAL_MIRROR) --xform s:^:diff-repo/: $(DIFF_MIRROR_CENTOS) $(DIFF_MIRROR_UBUNTU)


DIFF_MIRROR_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DIFF_MIRROR_ART_NAME))

ifdef DIFF_MIRROR_DEP_FILE
$(BUILD_DIR)/mirror/mirror-diff.done:
	# TODO: HERE WE NEED TO EXTRACT
	# mkdir -p $(ISOROOT)
	# tar xf $(DIFF_MIRROR_DEP_FILE) -C $(ISOROOT) --xform s:^centos-repo/::
	# createrepo -g $(ISOROOT)/comps.xml \
	# 	-u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/mirror-diff.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done \
		$(BUILD_DIR)/mirror/mirror_diff2.done
	$(ACTION.TOUCH)
endif
