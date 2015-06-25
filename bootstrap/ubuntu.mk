.PHONY: bootstrap-ubuntu clean-bootstrap-ubuntu

BOOTSTRAP_PKGS := \
	ubuntu-minimal \
	openssh-client \
	openssh-server \
	mcollective \
	ntp \
	live-boot \
	live-boot-initramfs-tools \
	vim \
	linux-image-generic-$(UBUNTU_KERNEL_FLAVOR) \
	linux-firmware \
	linux-firmware-nonfree

BOOTSTRAP_FUEL_PKGS :=\
	nailgun-agent \
	nailgun-mcagents \
	nailgun-net-check \
	fuel-agent

$(BUILD_DIR)/ubuntu-bootstrap/chroot.done: SANDBOX_DEB_PKGS:=$(BOOTSTRAP_PKGS)
$(BUILD_DIR)/ubuntu-bootstrap/chroot.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
$(BUILD_DIR)/ubuntu-bootstrap/chroot.done: export SANDBOX_UBUNTU_UP:=$(SANDBOX_UBUNTU_UP)
$(BUILD_DIR)/ubuntu-bootstrap/chroot.done: export SANDBOX_UBUNTU_DOWN:=$(SANDBOX_UBUNTU_DOWN)
$(BUILD_DIR)/ubuntu-bootstrap/chroot.done:
	sh -c "$${SANDBOX_UBUNTU_UP}"
	sh -c "$${SANDBOX_UBUNTU_DOWN}"


$(BUILD_DIR)/ubuntu-bootstrap/fuelinstall.done: FUEL_REPO_LOCAL:=$(LOCAL_MIRROR)/fuel/ubuntu
$(BUILD_DIR)/ubuntu-bootstrap/fuelinstall.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
# XXX: remove this dependency after Fuel stuff gets packaged properly
$(BUILD_DIR)/ubuntu-bootstrap/fuelinstall.done: $(BUILD_DIR)/mirror/fuel/ubuntu.done
$(BUILD_DIR)/ubuntu-bootstrap/fuelinstall.done: $(BUILD_DIR)/ubuntu-bootstrap/chroot.done \
		$(BUILD_DIR)/mirror/fuel/ubuntu.done
	echo "deb file:///mnt mos$(PRODUCT_VERSION) main" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/sources.list.d/fuel-local.list
	sudo mount -o bind $(FUEL_REPO_LOCAL) $(SANDBOX_UBUNTU)/mnt
	sudo mount -o remount,ro,bind $(SANDBOX_UBUNTU)/mnt
	sudo chroot $(SANDBOX_UBUNTU) env LC_ALL=C apt-get update
	sudo chroot $(SANDBOX_UBUNTU) env \
		LC_ALL=C \
		DEBIAN_FRONTEND=noninteractive \
		DEBCONF_NONINTERACTIVE_SEEN=true \
		apt-get install -y $(BOOTSTRAP_FUEL_PKGS)
	sudo umount $(SANDBOX_UBUNTU)/mnt
	sudo rm -f $(SANDBOX_UBUNTU)/etc/apt/sources.list.d/fuel-local.list


$(BUILD_DIR)/ubuntu-bootstrap/customize.done: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
$(BUILD_DIR)/ubuntu-bootstrap/customize.done: $(BUILD_DIR)/ubuntu-bootstrap/fuelinstall.done
	sudo mkdir -p -m 700 $(SANDBOX_UBUNTU)/root/.ssh
	sudo cp $(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub $(SANDBOX_UBUNTU)/root/.ssh/authorized_keys
# Setting root password into r00tme
	sudo sed -i -e '/^root/c\root:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' $(SANDBOX_UBUNTU)/etc/shadow
	sudo chmod 700 $(SANDBOX_UBUNTU)/root/.ssh
	sudo cp -r $(BUILD_DIR)/repos/nailgun/bin/send2syslog.py $(SANDBOX_UBUNTU)/usr/bin
	sudo rsync -rlptDK $(SOURCE_DIR)/bootstrap/ubuntu/files/ $(SANDBOX_UBUNTU)
	sudo rm -f $(SANDBOX_UBUNTU)/var/cache/apt/archives/*.deb
	sudo rm -f $(SANDBOX_UBUNTU)/var/log/bootstrap.log
	sudo rm -rf $(SANDBOX_UBUNTU)/run/*
	sudo rm -rf $(SANDBOX_UBUNTU)/tmp/*

$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.initramfs: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.initramfs: $(BUILD_DIR)/ubuntu-bootstrap/customize.done
	mkdir -p "$(@D)" && \
	cp $(SANDBOX_UBUNTU)/boot/initrd* $@

$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.linux: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.linux: $(BUILD_DIR)/ubuntu-bootstrap/customize.done
	mkdir -p "$(@D)" && \
	sudo chmod 644 $(SANDBOX_UBUNTU)/boot/vmlinuz* && \
	cp -a $(SANDBOX_UBUNTU)/boot/vmlinuz* $@

$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.squashfs: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.squashfs: $(BUILD_DIR)/bootstrap/ubuntu-bootstrap.linux \
		$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.initramfs
	mkdir -p "$(@D)" && \
	sudo rm -f $(SANDBOX_UBUNTU)/boot/initrd* && \
	sudo rm -f $(SANDBOX_UBUNTU)/boot/vmlinuz* && \
	sudo mksquashfs $(SANDBOX_UBUNTU) $@.tmp -no-progress -noappend && \
	mv $@.tmp $@


bootstrap-ubuntu: $(BUILD_DIR)/bootstrap/ubuntu-bootstrap.squashfs \
	$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.linux \
	$(BUILD_DIR)/bootstrap/ubuntu-bootstrap.initramfs


clean: clean-bootstrap-ubuntu

clean-bootstrap-ubuntu: SANDBOX_UBUNTU:=$(BUILD_DIR)/ubuntu-bootstrap/chroot
clean-bootstrap-ubuntu:
	@sudo umount $(SANDBOX_UBUNTU)/proc 2>/dev/null || true
	@sudo umount $(SANDBOX_UBUNTU)/mnt 2>/dev/null || true

