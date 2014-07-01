.PHONY: ubuntu_image clean_ubuntu_image

ubuntu_image: $(BUILD_DIR)/image/ubuntu/build.done

clean_ubuntu_image:
	-sudo umount -f $(BUILD_DIR)/image/ubuntu/ubuntu.img
	sudo rm -rf $(BUILD_DIR)/image/ubuntu

$(BUILD_DIR)/image/ubuntu/build.done: $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/image/ubuntu/build.done:
	@mkdir -p $(@D)
	truncate -s 1G $(BUILD_DIR)/image/ubuntu/ubuntu.img
	mkfs.ext4 -F $(BUILD_DIR)/image/ubuntu/ubuntu.img
	mkdir $(BUILD_DIR)/image/ubuntu/mnt
	sudo mount $(BUILD_DIR)/image/ubuntu/ubuntu.img $(BUILD_DIR)/image/ubuntu/mnt -o loop
# FIXME(kozhukalov): remove particular kernel version
	sudo debootstrap --no-check-gpg --arch=amd64 --include=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-3.11.0-18-generic,linux-headers-3.11.0-18,util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init precise $(BUILD_DIR)/image/ubuntu/mnt file://$(LOCAL_MIRROR)/ubuntu
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'initrd*' -exec cp '{}' $(BUILD_DIR)/image/ubuntu \;
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'vmlinuz*' -exec cp '{}' $(BUILD_DIR)/image/ubuntu \;
#	sudo rm -fr $(BUILD_DIR)/image/ubuntu/mnt/boot
	sudo umount -f $(BUILD_DIR)/image/ubuntu/ubuntu.img
	gzip $(BUILD_DIR)/image/ubuntu/ubuntu.img
	rm -fr $(BUILD_DIR)/image/ubuntu/mnt
	$(ACTION.TOUCH)
