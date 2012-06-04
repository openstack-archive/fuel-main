SUITE = precise
ARCH = i386

ifndef DEBOOTSTRAP_MIRROR
DEBOOTSTRAP_MIRROR = http://us.archive.ubuntu.com/ubuntu/
endif

ifndef DEBOOTSTRAP_INCLUDE
DEBOOTSTRAP_INCLUDE = less,vim,bash,net-tools,isc-dhcp-client,rsyslog,cron,iputils-ping,openssh-server,libhttpclient-ruby
endif

ifndef DEBOOTSTRAP_EXCLUDE
DEBOOTSTRAP_EXCLUDE =
endif

ifndef BUILD_BASEDIR
BUILD_BASEDIR = /var/tmp/build_basedir
endif

ifndef CACHE_BASEDIR
CACHE_BASEDIR = /var/tmp/cache_basedir
endif

ifndef INITRD_LOOP
INITRD_LOOP = $(BUILD_BASEDIR)/loop_$(SUITE)_$(ARCH)
endif

ifndef INITRD_MODULES
INITRD_MODULES = $(BUILD_BASEDIR)/modules_$(SUITE)_$(ARCH)
endif

ifndef INITRD_CACHE
INITRD_CACHE = $(CACHE_BASEDIR)/cache_$(SUITE)_$(ARCH)
endif

INITRD = $(BUILD_BASEDIR)/initrd_$(SUITE)_$(ARCH)
INITRDGZ = $(BUILD_BASEDIR)/initrd_$(SUITE)_$(ARCH).gz
INITRD_SIZE = 614400 #kilobytes



# HERE ARE SOME AUXILIARY VARIABLES
, := ,


build: $(INITRD)

initrd: $(INITRD)

cleanall: clean clean_cache


clean:
	rm -f $(INITRDGZ)
	rm -f $(INITRD)
	umount  $(INITRD_LOOP) || true
	rm -fr $(INITRD_LOOP)
	rm -fr $(INITRD_MODULES)

clean_cache:
	rm -fr $(INITRD_CACHE)

.PHONY: cleanall clean clean_cache


$(INITRD_MODULES): $(INITRD_CACHE)
	@echo "Extracting modules and firmware from packages ..."
	mkdir -p $(INITRD_MODULES)
	find $(INITRD_CACHE)/var/cache/apt/archives \( -name "linux-image*.deb" -o -name "linux-firmware*.deb" \) -exec dpkg -x {} $(INITRD_MODULES) \;

$(INITRD_CACHE):
	@echo "Creating debootstrap cache arch=$(ARCH) suite=$(SUITE)"
	debootstrap --download-only --variant=minbase \
--include=linux-image-generic,linux-firmware$(if $(DEBOOTSTRAP_INCLUDE),$(,)$(DEBOOTSTRAP_INCLUDE)) \
--arch=$(ARCH) $(SUITE) $(INITRD_CACHE) $(DEBOOTSTRAP_MIRROR)


$(INITRD): $(INITRD_CACHE) $(INITRD_MODULES)
	@echo "Creating zero file $(INITRD) 1024 * $(INITRD_SIZE) bytes size ..."
	dd if=/dev/zero of=$(INITRD) bs=1024 count=$(INITRD_SIZE)
	@echo "Creating ext2 file system in $(INITRD) ..."
	mkfs.ext2 -F -m0 $(INITRD)
	@echo "Creating loop directory to mount initrd file system ..."
	mkdir -p $(INITRD_LOOP)
	@echo "Mounting $(INITRD) to $(INITRD_LOOP)"
	mount -o loop -t ext2 $(INITRD) $(INITRD_LOOP)
	mkdir -p $(INITRD_LOOP)/var/cache/apt/archives
	@echo "Copying deb packages from cache to $(INITRD_LOOP) ..."
	cp -r $(INITRD_CACHE)/var/cache/apt/archives/*.deb $(INITRD_LOOP)/var/cache/apt/archives
	@echo "Debootstraping ..."
	debootstrap --variant=minbase \
$(if $(DEBOOTSTRAP_INCLUDE),--include=$(DEBOOTSTRAP_INCLUDE)) \
$(if $(DEBOOTSTRAP_EXCLUDE),--exclude=$(DEBOOTSTRAP_EXCLUDE)) \
--arch=$(ARCH) $(SUITE) $(INITRD_LOOP) $(DEBOOTSTRAP_MIRROR)
	@echo "Removing deb packages from $(INITRD_LOOP) ..."
	rm -f $(INITRD_LOOP)/var/cache/apt/archives/*.deb
	@echo "Copying modules and firmware ..."
	cp -r $(INITRD_MODULES)/lib/modules/* $(INITRD_LOOP)/lib/modules
	cp -r $(INITRD_MODULES)/lib/firmware/* $(INITRD_LOOP)/lib/firmware
	@echo "Unmounting $(INITRD_LOOP) ..."
	umount $(INITRD_LOOP)


$(INITRDGZ): $(INITRD)
	gzip -9 -c $(INITRD) > $(INITRDGZ)


