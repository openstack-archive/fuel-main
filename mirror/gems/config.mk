ifeq ($(LOCAL_MIRROR),)
$(error It seems that variable LOCAL_MIRROR was not set correctly)
endif

LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems