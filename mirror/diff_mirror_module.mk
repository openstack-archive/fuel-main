.PHONY: mirror_diff

mirror_diff: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/mirror_diff.done

$(LOCAL_MIRROR)/diff_mirror/centos/os/x86_64/Packages:
	@mkdir -p $(@)

$(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/main:
	@mkdir -p $(@)

$(BUILD_DIR)/mirror/mirror_diff.done: \
	$(LOCAL_MIRROR)/diff_mirror/centos/os/x86_64/Packages \
	$(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/main

	# NOTE: please, be sure that the folders definition have the below syntax
	# rsync -avrqSHP --compare-dest=/folder_old /folder_new/ /folder_result
	# otherwise rsync result will be completly wrong
	# centos
	rsync -avSHP --checksum --delete --compare-dest=/tmp/mirrors/5.1.1/centos/os/x86_64/Packages \
    $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages/ \
    $(LOCAL_MIRROR)/diff_mirror/centos/os/x86_64/Packages
  # ubuntu
	rsync -avSHP --checksum --delete --compare-dest=/tmp/mirrors/5.1.1/ubuntu/pool/main \
    $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main/ \
    $(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/main

	createrepo $(LOCAL_MIRROR)/diff_mirror/centos/os/x86_64/Packages -o $(LOCAL_MIRROR)/diff_mirror/centos/os/x86_64/

	dpkg-scanpackages -m $(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/main > $(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/Packages
	gzip -9c $(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/Packages > $(LOCAL_MIRROR)/diff_mirror/ubuntu/pool/Packages.gz

	$(ACTION.TOUCH)

# $(BUILD_DIR)/mirror/mirror_diff.done: \
# 	$(SOURCE_DIR)/mirror/create_update_mirrors.sh

# 	export DEBUG=True; \
# 	export OUTPUT_DIR=$(LOCAL_MIRROR)/; \
# 	$(SOURCE_DIR)/mirror/create_update_mirrors.sh $(LOCAL_MIRROR) 5.1
# 	$(ACTION.TOUCH)