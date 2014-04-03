SHELL=/bin/bash
BUILDTARGET=$(LOCAL_MIRROR_DOCKER_BASEURL)/cobbler
include $(SOURCE_DIR)/docker/cobbler/config
$(BUILD_DIR)/mirror/docker/cobbler.container:
	rm -rf "$(BUILD_DIR)/docker/cobbler"
	git clone --depth 1 --branch $(dockerref) $(dockerrepo) $(BUILD_DIR)/docker/cobbler
	if [ "$(puppetref)" != "none" -a "$(puppetref)" != "same" ]; then \
	  rm -rf $(BUILD_DIR)/docker/puppet ;   \
	  if grep -q "refs/changes" <<< "$(puppetref)"; then \
	    git clone --depth 50 --branch master $(puppetrepo) $(BUILD_DIR)/docker/puppet; \
	    pushd $(BUILD_DIR)/docker/puppet; \
	    git fetch $(FUELLIB_GERRIT_URL)  $(puppetref); \
	    git cherry-pick FETCH_HEAD; \
	    popd; \
	  else \
	    git clone --depth 1 --branch $(puppetref) $(puppetrepo) $(BUILD_DIR)/docker/puppet; \
	  \
	  fi; \
	  rm -rf "$(BUILD_DIR)/docker/cobbler/etc/puppet/modules"; \
	  mkdir -p "$(BUILD_DIR)/docker/cobbler/etc/puppet/modules"; \
	  cp -R $(BUILD_DIR)/docker/puppet/deployment/puppet/* $(BUILD_DIR)/docker/cobbler/etc/puppet/modules; \
	elif [ "$(puppetref)" = "same" ];then \
	  mkdir -p "$(BUILD_DIR)/docker/cobbler/etc/puppet/modules"; \
	  pushd "$(BUILD_DIR)/docker/cobbler/etc/puppet/modules"; \
	  git init puppet; \
	  git remote add puppet $(FUELLIB_REPO); \
	  git fetch puppet $(FUELLIB_COMMIT); \
	  git checkout FETCH_HEAD; \
	  popd; \
	fi;   
	pushd $(BUILD_DIR)/docker/
	sed -i -e "s]@@MIRROR_CENTOS@@]$(MIRROR_CENTOS_OS_BASEURL)]" $(BUILD_DIR)/docker/cobbler/Dockerfile
	docker build -t fuel/cobbler  $(BUILD_DIR)/docker/cobbler
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/docker/cobbler.compress: 
	docker save fuel/cobbler | $(DOCKER_ARCHIVER) > $(addsuffix $(DOCKER_ARCHIVE_SUFFIX),$(BUILDTARGET))
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/docker/cobbler.done: \
	$(BUILD_DIR)/mirror/docker/cobbler.container \
	$(BUILD_DIR)/mirror/docker/cobbler.compress
	$(ACTION.TOUCH)
