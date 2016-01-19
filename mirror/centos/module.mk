# This module downloads required upstream rpm packages and creates rpm repository.
include $(SOURCE_DIR)/mirror/centos/repo.mk
# This module downloads centos installation images.
include $(SOURCE_DIR)/mirror/centos/boot.mk
# This module downloads MOS rpm repository
include $(SOURCE_DIR)/mirror/centos/mos-repo.mk
# This module downloads extra rpm repositories
include $(SOURCE_DIR)/mirror/centos/extra-repos.mk

$(BUILD_DIR)/mirror/centos/build.done: \
		$(BUILD_DIR)/mirror/centos/repo.done \
		$(BUILD_DIR)/mirror/centos/boot.done \
		$(BUILD_DIR)/mirror/centos/mos-repo.done \
		$(BUILD_DIR)/mirror/centos/extra-repos.done
	$(ACTION.TOUCH)

mirror-centos: $(BUILD_DIR)/mirror/centos/build.done
repo-centos: $(BUILD_DIR)/mirror/centos/repo.done
repo-mos-centos: $(BUILD_DIR)/mirror/centos/mos-repo.done
extra-repos-centos: $(BUILD_DIR)/mirror/centos/extra-repos.done

.PHONY: mirror-centos repo-centos repo-mos-centos extra-repos-centos
