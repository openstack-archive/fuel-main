ifndef BOOTSTRAP_REBUILD
BOOTSTRAP_REBUILD:=1
endif

MIRROR_URL:=http://srv08-srt.srt.mirantis.net/mirror

ifndef IGNORE_MIRROR
IGNORE_MIRROR:=0
endif

ifndef LOCAL_MIRROR
LOCAL_MIRROR:=local_mirror
endif

iso.path:=$(BUILD_DIR)/iso/nailgun-centos-6.3-amd64.iso

bootstrap.linux:=$(BUILD_DIR)/bootstrap/linux
bootstrap.initrd:=$(BUILD_DIR)/bootstrap/initrd.gz

