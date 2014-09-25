.PHONY: mirror_diff

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
