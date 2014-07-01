.PHONY: ubuntu_image clean_ubuntu_image

ubuntu_image: $(BUILD_DIR)/image/ubuntu/build.done

clean_ubuntu_image:
	sudo rm -rf $(BUILD_DIR)/image/ubuntu

$(BUILD_DIR)/image/ubuntu/build.done: $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/image/ubuntu/build.done:
	sudo mkdir -p $(BUILD_DIR)/image/ubuntu
	sudo truncate -s 1G $(BUILD_DIR)/image/ubuntu/build.img
	sudo mkfs.ext4 -F $(BUILD_DIR)/image/ubuntu/build.img
	sudo mkdir $(BUILD_DIR)/image/ubuntu/mnt
	sudo mount $(BUILD_DIR)/image/ubuntu/build.img $(BUILD_DIR)/image/ubuntu/mnt -o loop
	# sudo debootstrap --no-check-gpg --arch=amd64 --include=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-3.11.0-18-generic,linux-headers-3.11.0-18,util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init precise $(BUILD_DIR)/image/ubuntu file://$(LOCAL_MIRROR)/ubuntu
	sudo debootstrap --no-check-gpg --arch=amd64 --include=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-3.11.0-18-generic,linux-headers-3.11.0-18,util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc precise $(BUILD_DIR)/image/ubuntu/mnt file://$(LOCAL_MIRROR)/ubuntu
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'initrd*' -exec cp '{}' $(BUILD_DIR)/image/ubuntu \;
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'vmlinuz*' -exec cp '{}' $(BUILD_DIR)/image/ubuntu \;
	sudo rm -fr $(BUILD_DIR)/image/ubuntu/mnt/boot
	sudo umount -f $(BUILD_DIR)/image/ubuntu/build.img
	sudo rm -fr $(BUILD_DIR)/image/ubuntu/mnt
	sudo $(ACTION.TOUCH)
