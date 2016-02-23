.PHONY: mirror mirror-centos mirror-ubuntu clean clean-mirror make-changelog

mirror: $(BUILD_DIR)/mirror.done
mirror-ubuntu: $(BUILD_DIR)/mirror-ubuntu.done
mirror-centos: $(BUILD_DIR)/mirror-centos.done
mirror-changelog: $(BUILD_DIR)/mirror-changelog.done

clean: clean-mirror
clean-mirror:
	rm -rf $(BUILD_DIR)/mirror

$(BUILD_DIR)/mirror.done: \
		$(BUILD_DIR)/mirror-centos.done \
		$(BUILD_DIR)/mirror-ubuntu.done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror-changelog.done: $(BUILD_DIR)/mirror.done
	bash -c "export LOCAL_MIRROR=$(LOCAL_MIRROR); \
		$(SOURCE_DIR)/report-changelog.sh"
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror-centos.done: \
		$(BUILD_DIR)/mirror-centos-mos.done \
		$(BUILD_DIR)/mirror-centos-upstream.done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror-centos-mos.done:
	mkdir -p $(LOCAL_MIRROR)
	packetary --threads-num 10 clone -t rpm -r $(RPM_MOS_REPOS_YAML) -f $(RPM_MOS_FILTERS_YAML) -d $(LOCAL_MIRROR)
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror-centos-upstream.done: $(BUILD_DIR)/mirror-centos-mos.done
	mkdir -p $(LOCAL_MIRROR)
	packetary --threads-num 10 clone -t rpm -r $(RPM_REPOS_YAML) -p $(RPM_PACKAGES_YAML) -d $(LOCAL_MIRROR)
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror-ubuntu.done:
	mkdir -p $(LOCAL_MIRROR)
	packetary --threads-num 10 clone -t deb -r $(DEB_MOS_REPOS_YAML) -f $(DEB_MOS_FILTERS_YAML) -d $(LOCAL_MIRROR)
	$(ACTION.TOUCH)
