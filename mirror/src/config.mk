SRC_URLS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)

ifeq ($(LOCAL_MIRROR),)
$(error It seems that variable LOCAL_MIRROR was not set correctly)
endif

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src