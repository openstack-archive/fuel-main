ifndef INITRD_TMP
INITRD_TMP = /var/tmp/.initrd
endif

ifndef INITRD_TMP_MODULES
INITRD_TMP_MODULES = /var/tmp/.initrd_modules
endif

INITRD_INCLUDE = less,vim,zsh,bash
INITRD_EXCLUDE = 
INITRD_SUITE = precise
INITRD_ARCH = i386
INITRD_MIRROR = http://us.archive.ubuntu.com/ubuntu/
INITRD_DEV = initrd
INITRD_GZ = initrd.gz
INITRD_SIZE = 307200 #kilobytes


ifndef INITRD_CACHE
INITRD_CACHE = /var/tmp/.initrd_cache_$(INITRD_SUITE)_$(INITRD_ARCH)
endif



cleanall: clean_initrdgz clean_initrddev clean_initrdtmp clean_initrdcache clean_initrdmodules


clean_initrdgz:
	rm -f $(INITRD_GZ)

clean_initrddev:
	rm -f $(INITRD_DEV)

clean_initrdtmp:
	rm -fr $(INITRD_TMP)

clean_initrdcache:
	rm -fr $(INITRD_CACHE)

clean_initrdmodules:
	rm -f $(LINUX_PACKAGE_NAME)
	rm -rf linux-image-generic

initrddev: clean_initrddev
	dd if=/dev/zero of=$(INITRD_DEV) bs=1024 count=$(INITRD_SIZE)

initrdfs: initrddev
	mkfs.ext2 -F -m0 $(INITRD_DEV)

initrdmodules: clean_initrdmodules $(INITRD_CACHE)
	mkdir -p $(INITRD_TMP_MODULES)
	find $(INITRD_CACHE)/var/cache/apt/archives \( -name "linux-image*.deb" -o -name "linux-firmware*.deb" \) -exec dpkg -x {} $(INITRD_TMP_MODULES) \;

initrdcache:
	sudo debootstrap --download-only --variant=minbase --include=linux-image-generic,linux-firmware --arch=$(INITRD_ARCH) $(INITRD_SUITE) $(INITRD_CACHE) $(INITRD_MIRROR)


initrd: initrddev initrdfs initrdcache initrdmodules
	mkdir -p $(INITRD_TMP)
	mount -o loop -t ext2 $(INITRD_DEV) $(INITRD_TMP)
	mkdir -p $(INITRD_TMP)/var/cache/apt/archives
	cp -r $(INITRD_CACHE)/var/cache/apt/archives/*.deb $(INITRD_TMP)/var/cache/apt/archives
	sudo debootstrap --variant=minbase --include=$(INITRD_INCLUDE) --arch=$(INITRD_ARCH) $(INITRD_SUITE) $(INITRD_TMP) $(INITRD_MIRROR)
	rm -f $(INITRD_TMP)/var/cache/apt/archives/*.deb
	cp -r $(INITRD_TMP_MODULES)/lib/modules/* $(INITRD_TMP)/lib/modules
	cp -r $(INITRD_TMP_MODULES)/lib/firmware/* $(INITRD_TMP)/lib/firmware
	umount $(INITRD_TMP)


initrdgz: clean_initrdgz initrd
	gzip -9 -c $(INITRD_DEV) > $(INITRD_GZ)


