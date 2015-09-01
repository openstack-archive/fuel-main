containers:=astute cobbler mcollective nailgun keystone nginx ostf rsync rsyslog rabbitmq postgres
REPO_CONTAINER:=fuel-repo-container
DOCKER_ART_NAME?=fuel-images.tar.lrz
PRODUCT_VERSION?=7.0

.DELETE_ON_ERROR: $(BUILD_DIR)/docker/$(DOCKER_ART_NAME)
.DELETE_ON_ERROR: $(BUILD_DIR)/docker/fuel-images.tar

# Lrzip all containers into single archive
$(BUILD_DIR)/docker/build.done: \
		$(BUILD_DIR)/docker/fuel-centos.done \
		$(BUILD_DIR)/docker/sources.done
	sudo docker save fuel/centos busybox $(foreach cnt,$(containers), fuel/$(cnt)_$(PRODUCT_VERSION)) > $(BUILD_DIR)/docker/fuel-images.tar
	lrzip -L2 -U -D -f $(BUILD_DIR)/docker/fuel-images.tar -o $(BUILD_DIR)/docker/$(DOCKER_ART_NAME)
	rm -f $(BUILD_DIR)/docker/fuel-images.tar
	sudo docker rm -f "$(REPO_CONTAINER)" || true
	mkdir -p $(@D)
	touch $@

define build_container
$(BUILD_DIR)/docker/build.done: $(BUILD_DIR)/docker/$1.done
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/docker/fuel-centos.done \
		$(BUILD_DIR)/docker/repo-container-up.done
	mkdir -p "$(BUILD_DIR)/docker/containers" && \
	rm -rf $(BUILD_DIR)/docker/$1 && \
	cp -a $(SOURCE_DIR)/$1 $(BUILD_DIR)/docker/$1 && \
	REPO_PORT=`sudo docker port $(REPO_CONTAINER) 80 | cut -d':' -f2` && \
	sed -e "s/_PORT_/$$$${REPO_PORT}/" -i $(BUILD_DIR)/docker/$1/Dockerfile && \
	mkdir -p $(BUILD_DIR)/docker/$1/etc/fuel && \
	cp $(SOURCE_DIR)/docker-astute.yaml $(BUILD_DIR)/docker/$1/etc/fuel/astute.yaml && \
	sudo docker build --force-rm -t fuel/$1_$(PRODUCT_VERSION) $(BUILD_DIR)/docker/$1
	mkdir $$(@D)
	touch $$@
endef

$(BUILD_DIR)/docker/base-images.done: $(BUILD_DIR)/docker-mirror/build.done
	for container in $(LOCAL_MIRROR_DOCKER_BASEURL)/*.xz; do \
		xz -dkc -T0 $$container | sudo docker load; \
	done
	mkdir -p $(@D)
	touch $@

$(BUILD_DIR)/docker/fuel-centos.done: \
		$(BUILD_DIR)/docker/base-images.done \
	rm -rf $(BUILD_DIR)/docker/fuel-centos-build && \
	cp -a $(SOURCE_DIR)/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build && \
	sudo docker build -t fuel/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build && \
	mkdir -p $(BUILD_DIR)/docker/fuel-centos/ && \
	echo "Generating fuel/centos base image. Refer to $(BUILD_DIR)/docker/fuel-centos-build.log if it fails." && \
	sudo docker -D run --net=bridge --rm -a stdout -a stderr -i -t --privileged -v $(LOCAL_MIRROR_CENTOS):/repo:ro -v $(BUILD_DIR)/docker/fuel-centos:/export fuel/fuel-centos-build 2>&1 > $(BUILD_DIR)/docker/fuel-centos-build.log && \
	sudo $(SOURCE_DIR)/fuel-centos-build/img2docker.sh $(BUILD_DIR)/docker/fuel-centos/fuel-centos.img fuel/centos
	mkdir -p $(@D)
	touch $@

$(BUILD_DIR)/docker/repo-container-up.done: \
		$(BUILD_DIR)/docker/fuel-centos.done
	-sudo docker rm -f "$(REPO_CONTAINER)"
	sudo docker -D run -d -p 80 -v $(LOCAL_MIRROR_CENTOS):/var/www/html --name "$(REPO_CONTAINER)" fuel/centos /usr/sbin/apachectl -DFOREGROUND
	REPO_PORT=`sudo docker port $(REPO_CONTAINER) 80 | cut -d':' -f2` && \
	wget -t10 -T1 --waitretry 1 --retry-connrefused --no-proxy http://127.0.0.1:$${REPO_PORT}/os/x86_64/repodata/repomd.xml
	mkdir -p $(@D)
	touch $@

$(BUILD_DIR)/docker/sources.done: \
		$(find-files $(SOURCE_DIR)/docker)
	mkdir -p $(BUILD_DIR)/docker/sources
	find $(SOURCE_DIR) -mindepth 1 -type d -not -name '*fuel-centos-build*' | xargs cp -r --target-directory=$(BUILD_DIR)/docker/sources
	mkdir -p $(@D)
	touch $@

$(foreach cnt,$(containers),$(eval $(call build_container,$(cnt))))
