# CENTOS REPOSITORIES SETTINGS

CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64
CENTOS_MIRROR:=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
CENTOS_NETINSTALL:=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)/isos/$(CENTOS_ARCH)
CENTOS_GPG:=http://mirror.yandex.ru/centos

REPOMIRROR:=$(MIRROR_URL)/centos
CENTOSMIRROR:=http://mirror.yandex.ru/centos
EPELMIRROR:=http://mirror.yandex.ru/epel
RPMFORGEMIRROR:=http://apt.sw.be/redhat

CENTOS_REPO_DIR:=$(LOCAL_MIRROR)/centos/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)/
CENTOS_ISO_DIR:=$(LOCAL_MIRROR)/centos/$(CENTOS_RELEASE)/isos/$(CENTOS_ARCH)/

ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest splash.jpg vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img efidisk.img install.img
EFI_FILES:=BOOTX64.conf BOOTX64.efi splash.xpm.gz
BOOTSTRAP_FILES:=initramfs.img linux
NETINSTALL_ISO:=CentOS-$(CENTOS_RELEASE)-$(CENTOS_ARCH)-minimal-EFI.iso

# OUR PACKAGES VERSIONS

NAILGUN_VERSION:=0.1.0
NAILY_VERSION:=0.0.1
ASTUTE_VERSION:=0.0.1
