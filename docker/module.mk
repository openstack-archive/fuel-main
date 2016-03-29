.PHONY: docker
containers:=astute cobbler mcollective nailgun keystone nginx ostf rsync rsyslog rabbitmq postgres
REPO_CONTAINER:=fuel-repo-container

docker: $(ARTS_DIR)/$(DOCKER_ART_NAME)

$(ARTS_DIR)/$(DOCKER_ART_NAME): \
		$(BUILD_DIR)/docker/build.done
	mkdir -p $(@D)
	cp $(BUILD_DIR)/docker/$(DOCKER_ART_NAME) $@

DOCKER_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DOCKER_ART_NAME))

ifdef DOCKER_DEP_FILE
$(BUILD_DIR)/docker/build.done: \
		$(DOCKER_DEP_FILE) \
		$(BUILD_DIR)/docker/sources.done
	mkdir -p $(@D)
	cp $(DOCKER_DEP_FILE) $(BUILD_DIR)/docker/$(DOCKER_ART_NAME)
	$(ACTION.TOUCH)
else
# Lrzip all containers into single archive
$(BUILD_DIR)/docker/build.done: \
		$(BUILD_DIR)/docker/fuel-centos.done \
		$(BUILD_DIR)/docker/sources.done
	sudo docker save fuel/centos busybox $(foreach cnt,$(containers), fuel/$(cnt)_$(PRODUCT_VERSION):latest) > $(BUILD_DIR)/docker/fuel-images.tar
	lrzip -L2 -U -D -f $(BUILD_DIR)/docker/fuel-images.tar -o $(BUILD_DIR)/docker/$(DOCKER_ART_NAME)
	rm -f $(BUILD_DIR)/docker/fuel-images.tar
	sudo docker rm -f "$(REPO_CONTAINER)" || true
	$(ACTION.TOUCH)
endif

define build_container
ifndef DOCKER_DEP_FILE
$(BUILD_DIR)/docker/build.done: $(BUILD_DIR)/docker/$1.done
endif
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/docker/fuel-centos.done \
		$(BUILD_DIR)/iso/isoroot/$(VERSION_YAML_ART_NAME) \
		$(BUILD_DIR)/docker/repo-container-up.done
	@echo ""
	@echo "========================================"
	@echo "Building container '$1'"
	mkdir -p "$(BUILD_DIR)/docker/containers"
	rm -rf $(BUILD_DIR)/docker/$1
	cp -a $(SOURCE_DIR)/docker/$1 $(BUILD_DIR)/docker/$1
	REPO_PORT=`sudo docker port $(REPO_CONTAINER) 80 | cut -d':' -f2` && \
		sed -e "s/_PORT_/$$$${REPO_PORT}/" -i $(BUILD_DIR)/docker/$1/Dockerfile
	test -n "$(EXTRA_RPM_REPOS)" || sed -e "/_EXTRA_RPM_REPOS_/d" -i $(BUILD_DIR)/docker/$1/Dockerfile
	sed -e "s|_EXTRA_RPM_REPOS_|$(EXTRA_RPM_REPOS)|" -i $(BUILD_DIR)/docker/$1/Dockerfile
	mkdir -p $(BUILD_DIR)/docker/$1/etc/fuel
	cp $(BUILD_DIR)/iso/isoroot/version.yaml $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	sed -e 's/production:.*/production: "docker-build"/' -i $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	cp $(SOURCE_DIR)/docker/docker-astute.yaml $(BUILD_DIR)/docker/$1/etc/fuel/astute.yaml
	sudo docker build --force-rm -t fuel/$1_$(PRODUCT_VERSION) $(BUILD_DIR)/docker/$1
	sudo docker run --name=FUEL_$1_$(PRODUCT_VERSION) \
		--net=bridge -d -i -t --privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro fuel/$1_$(PRODUCT_VERSION)
	sudo docker exec -i FUEL_$1_$(PRODUCT_VERSION) /usr/local/bin/setup.sh 2>&1 \
		|| (echo "CONTAINER BUILD FAILED, container '$1'"; exit 1)
	sudo docker commit FUEL_$1_$(PRODUCT_VERSION) fuel/$1_$(PRODUCT_VERSION):latest
	sudo docker stop FUEL_$1_$(PRODUCT_VERSION)
	@echo "CONTAINER BUILD SUCCEEDED, container '$1'."
	@echo "========================================"
	@echo ""
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/docker/base-images.done: \
		$(BUILD_DIR)/mirror/docker/build.done
	for container in $(LOCAL_MIRROR_DOCKER_BASEURL)/*.xz; do xz -dkc -T0 $$container | sudo docker load; done
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/fuel-centos.done: export docker_upstream_mirror:=$(yum_upstream_repo)
$(BUILD_DIR)/docker/fuel-centos.done: \
		$(BUILD_DIR)/docker/base-images.done \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/packages/rpm/build.done
	rm -rf $(BUILD_DIR)/docker/fuel-centos-build
	cp -a $(SOURCE_DIR)/docker/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build
	echo "$${docker_upstream_mirror}" > $(BUILD_DIR)/docker/fuel-centos-build/upstream.repo
	test -n "$(EXTRA_RPM_REPOS)" || sed -e "/_EXTRA_RPM_REPOS_/d" -i $(BUILD_DIR)/docker/fuel-centos-build/Dockerfile
	sed -e "s|_CENTOS_RELEASE_|$(CENTOS_RELEASE)|g" -i $(BUILD_DIR)/docker/fuel-centos-build/Dockerfile
	sed -e "s|_EXTRA_RPM_REPOS_|$(EXTRA_RPM_REPOS)|" -i $(BUILD_DIR)/docker/fuel-centos-build/Dockerfile
	sudo docker build -t fuel/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build
	mkdir -p $(BUILD_DIR)/docker/fuel-centos/
	echo ">>> Generating fuel/centos base image..."
	sudo docker -D run --name=FUEL_CENTOS_$(PRODUCT_VERSION) --net=bridge -d -i -t --privileged \
		-v $(LOCAL_MIRROR_CENTOS):/repo:ro \
		-v $(LOCAL_MIRROR_MOS_CENTOS):/mos-repo:ro \
		-v $(LOCAL_MIRROR)/extra-repos:/extra-repos:ro \
		-v $(BUILD_DIR)/docker/fuel-centos:/export \
		fuel/fuel-centos-build
	sudo docker exec -i FUEL_CENTOS_$(PRODUCT_VERSION) /usr/local/bin/start.sh 2>&1
	echo "<<< Image generated successfully."
	echo ">>> Converting image..."
	sudo $(SOURCE_DIR)/docker/fuel-centos-build/img2docker.sh $(BUILD_DIR)/docker/fuel-centos/fuel-centos.img fuel/centos
	echo "<<< Image converted successfully."
	echo "$@ done."
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/repo-container-up.done: \
		$(BUILD_DIR)/docker/fuel-centos.done
	-sudo docker rm -f "$(REPO_CONTAINER)"
	sudo docker -D run --name "$(REPO_CONTAINER)" -d -p 80 \
		-v $(LOCAL_MIRROR_CENTOS):/var/www/html/repo \
		-v $(LOCAL_MIRROR_MOS_CENTOS):/var/www/html/mos-repo \
		-v $(LOCAL_MIRROR)/extra-repos:/var/www/html/extra-repos \
		fuel/centos /usr/sbin/apachectl -DFOREGROUND
	REPO_PORT=`sudo docker port $(REPO_CONTAINER) 80 | cut -d':' -f2` && \
	wget -t10 -T1 -O /dev/null --waitretry 1 --retry-connrefused --no-proxy http://127.0.0.1:$${REPO_PORT}/repo/os/x86_64/repodata/repomd.xml && \
	wget -t10 -T1 -O /dev/null --waitretry 1 --retry-connrefused --no-proxy http://127.0.0.1:$${REPO_PORT}/mos-repo/repodata/repomd.xml
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/sources.done: \
		$(find-files $(SOURCE_DIR)/docker)
	mkdir -p $(BUILD_DIR)/docker/sources $(BUILD_DIR)/docker/utils
	find $(SOURCE_DIR)/docker -mindepth 1 -type d -not -name '*fuel-centos-build*' | xargs cp -r --target-directory=$(BUILD_DIR)/docker/sources
	$(ACTION.TOUCH)

$(foreach cnt,$(containers),$(eval $(call build_container,$(cnt))))
