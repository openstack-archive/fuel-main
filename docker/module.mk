.PHONY: docker
containers:=astute cobbler mcollective nailgun keystone nginx ostf rsync rsyslog rabbitmq postgres

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
	sudo docker save fuel/centos busybox $(foreach cnt,$(containers), fuel/$(cnt)_$(PRODUCT_VERSION)) > $(BUILD_DIR)/docker/fuel-images.tar
	lrzip -L2 -U -D -f $(BUILD_DIR)/docker/fuel-images.tar -o $(BUILD_DIR)/docker/$(DOCKER_ART_NAME)
	rm -f $(BUILD_DIR)/docker/fuel-images.tar
	$(ACTION.TOUCH)
endif

RANDOM_PORT:=$(shell shuf -i 9000-65000 -n 1)

define build_container
ifndef DOCKER_DEP_FILE
$(BUILD_DIR)/docker/build.done: $(BUILD_DIR)/docker/$1.done
endif
$(eval RANDOM_PORT:=$(shell echo $$(($(RANDOM_PORT)+1))))
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/iso/isoroot-files.done \
		$(BUILD_DIR)/docker/base-images.done
	(cd $(LOCAL_MIRROR_CENTOS) && python $(SOURCE_DIR)/utils/simple_http_daemon.py $(RANDOM_PORT) /tmp/simple_http_daemon_$(RANDOM_PORT).pid)
	REPO_CONT_ID=`sudo docker -D run -d -p 80 fuel/centos yum install -y httpd;apachectl -d -DFOREGROUND`
	RANDOM_PORT=`sudo docker port $$REPO_CONT_ID 80`
	mkdir -p "$(BUILD_DIR)/docker/containers"
	rm -rf $(BUILD_DIR)/docker/$1
	cp -a $(SOURCE_DIR)/docker/$1 $(BUILD_DIR)/docker/$1
	sed -e "s/_PORT_/$(RANDOM_PORT)/" -i $(BUILD_DIR)/docker/$1/Dockerfile
	mkdir -p $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	mkdir -p $(BUILD_DIR)/docker/$1/etc/fuel
	cp $(BUILD_DIR)/iso/isoroot/version.yaml $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	sed -e 's/production:.*/production: "docker-build"/' -i $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	cp $(SOURCE_DIR)/docker/docker-astute.yaml $(BUILD_DIR)/docker/$1/etc/fuel/astute.yaml
	rsync -a $(BUILD_DIR)/repos/fuellib/deployment/puppet/* $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	sudo docker build --force-rm -t fuel/$1_$(PRODUCT_VERSION) $(BUILD_DIR)/docker/$1
	kill `cat /tmp/simple_http_daemon_$(RANDOM_PORT).pid`
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/docker/base-images.done: \
		$(BUILD_DIR)/mirror/docker/build.done
	for container in $(LOCAL_MIRROR_DOCKER_BASEURL)/*.xz; do xz -dkc -T0 $$container | sudo docker load; done
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/fuel-centos.done: \
		$(BUILD_DIR)/docker/base-images.done \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/packages/rpm/build.done
	REPO_CONT_ID=`sudo docker -D run -d -p 80 centos yum install -y httpd;apachectl -d -DFOREGROUND`
	RANDOM_PORT=`sudo docker port $$REPO_CONT_ID 80`
	rm -rf $(BUILD_DIR)/docker/fuel-centos-build
	cp -a $(SOURCE_DIR)/docker/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build
	sed -e "s/_PORT_/$$RANDOM_PORT/" -i $(BUILD_DIR)/docker/fuel-centos-build/Dockerfile
	sudo docker build -t fuel/fuel-centos-build $(BUILD_DIR)/docker/fuel-centos-build
	sudo docker rm -f $$REPO_CONT_ID
	mkdir -p "$(BUILD_DIR)/docker/centos/output"
	echo "Generating fuel/centos base image. Refer to $(BUILD_DIR)/docker/fuel-centos-build.log if it fails."
	sudo docker -D run --rm -a stdout -a stderr -i -t --privileged -v $(LOCAL_MIRROR_CENTOS)/os/x86_64/:/repo:ro -v $(BUILD_DIR)/docker/centos/output:/export fuel/fuel-centos-build 2>&1 > $(BUILD_DIR)/docker/fuel-centos-build.log
	sudo $(SOURCE_DIR)/docker/fuel-centos-build/img2docker.sh $(BUILD_DIR)/docker/centos/output/fuel-centos.img fuel/centos
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/sources.done: \
		$(find-files $(SOURCE_DIR)/docker)
	mkdir -p $(BUILD_DIR)/docker/sources $(BUILD_DIR)/docker/utils
	find $(SOURCE_DIR)/docker -mindepth 1 -type d -not -name '*fuel-centos-build*' | xargs cp -r --target-directory=$(BUILD_DIR)/docker/sources
	cp -r $(SOURCE_DIR)/utils/simple_http_daemon.py $(BUILD_DIR)/docker/utils
	$(ACTION.TOUCH)

$(foreach cnt,$(containers),$(eval $(call build_container,$(cnt))))
