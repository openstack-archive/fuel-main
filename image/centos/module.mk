.PHONY: centos_image clean_centos_image

centos_image: $(BUILD_DIR)/image/centos/build.done

clean_centos_image:
	-sudo umount $(BUILD_DIR)/image/centos/SANDBOX/proc
	-sudo umount $(BUILD_DIR)/image/centos/SANDBOX/dev
	sudo rm -rf $(BUILD_DIR)/image/centos

$(BUILD_DIR)/image/centos/build.done: $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/image/centos/build.done: SANDBOX:=$(BUILD_DIR)/image/centos/SANDBOX
$(BUILD_DIR)/image/centos/build.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/image/centos/build.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/image/centos/build.done:
	@mkdir -p $(@D)
	sudo sh -c "$${SANDBOX_UP}"
	sudo yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --nogpgcheck install tar python-setuptools git python-imgcreate python-argparse
	sudo cp /etc/mtab $(SANDBOX)/etc/mtab
	sudo mkdir -p $(SANDBOX)/run/shm
	sudo cp $(SOURCE_DIR)/image/centos/build_centos_image.py $(SANDBOX)/build_centos_image.py
	sudo cp $(SOURCE_DIR)/image/centos/centos.ks $(SANDBOX)/centos.ks
	sudo mkdir -p $(SANDBOX)/mirror
	sudo mount -o bind $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(SANDBOX)/mirror
	sudo chroot $(SANDBOX) python build_centos_image.py -k centos.ks -n centos -e
	sudo mv $(SANDBOX)/centos.img $(BUILD_DIR)/image/centos/
	sudo gzip $(BUILD_DIR)/image/centos/centos.img
	sudo mv $(SANDBOX)/initramfs*.img $(BUILD_DIR)/image/centos/
	sudo mv $(SANDBOX)/vmlinuz* $(BUILD_DIR)/image/centos/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)
