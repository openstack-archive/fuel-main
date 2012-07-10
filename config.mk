
BINARIES_DIR:=binaries
ifndef BOOTSTRAP_REBUILD
BOOTSTRAP_REDUILD:=0
endif
iso.path:=$(BUILD_DIR)/iso/nailgun-ubuntu-12.04-amd64.iso
centos.path=/home/jenkins/CENTOS62-base.img
bootstrap.linux:=$(BUILD_DIR)/bootstrap/linux
bootstrap.initrd:=$(BUILD_DIR)/bootstrap/initrd.gz

