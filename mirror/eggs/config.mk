ifeq ($(LOCAL_MIRROR),)
$(error It seems that variable LOCAL_MIRROR was not set correctly)
endif

ifeq ($(LOCAL_MIRROR_CENTOS_OS_BASEURL),)
$(error It seems that variable LOCAL_MIRROR_CENTOS_OS_BASEURL was not set correctly)
endif

LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)

# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS:=http://pypi.python.org/simple
