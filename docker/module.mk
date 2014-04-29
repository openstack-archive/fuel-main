.PHONY: docker

ISOROOT:=$(BUILD_DIR)/iso/isoroot
RANDOM_PORT:=$(shell shuf -i 9000-65000 -n 1)

docker: $(BUILD_DIR)/docker/build.done

define build_container
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/iso/isoroot-files.done
ifeq ($(DOCKER_PREBUILT),0)
	(cd $(LOCAL_MIRROR_CENTOS) && python $(SOURCE_DIR)/utils/simple_http_daemon.py $(RANDOM_PORT) /tmp/simple_http_daemon_$(RANDOM_PORT).pid)
	mkdir -p "$(BUILD_DIR)/docker/containers"
	rm -rf $(BUILD_DIR)/docker/$1
	cp -a $(SOURCE_DIR)/docker/$1 $(BUILD_DIR)/docker/$1
	sed -e "s/_PORT_/$(RANDOM_PORT)/" -i $(BUILD_DIR)/docker/$1/Dockerfile
	mkdir -p $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	mkdir -p $(BUILD_DIR)/docker/$1/etc/fuel
	cp $(ISOROOT)/version.yaml $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	sed -e 's/production:.*/production: "docker-build"/' -i $(BUILD_DIR)/docker/$1/etc/fuel/version.yaml
	cp $(SOURCE_DIR)/docker/docker-astute.yaml $(BUILD_DIR)/docker/$1/etc/fuel/astute.yaml
	rsync -a $(BUILD_DIR)/repos/fuellib/deployment/puppet/* $(BUILD_DIR)/docker/$1/etc/puppet/modules/
	sudo docker build -t fuel/$1_$(PRODUCT_VERSION) $(BUILD_DIR)/docker/$1
	sudo docker save fuel/$1_$(PRODUCT_VERSION) > $(BUILD_DIR)/docker/containers/$1.tar
	kill `cat /tmp/simple_http_daemon_$(RANDOM_PORT).pid`
endif
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/docker/busybox.done:
	sudo docker pull busybox
	mkdir -p "$(BUILD_DIR)/docker/containers"
	sudo docker save busybox > $(BUILD_DIR)/docker/containers/busybox.tar
	$(ACTION.TOUCH)

# Lrzip all containers into single archive
$(BUILD_DIR)/docker/build.done: \
		$(BUILD_DIR)/docker/astute.done \
		$(BUILD_DIR)/docker/cobbler.done \
		$(BUILD_DIR)/docker/mcollective.done \
		$(BUILD_DIR)/docker/nailgun.done \
		$(BUILD_DIR)/docker/nginx.done \
		$(BUILD_DIR)/docker/ostf.done \
		$(BUILD_DIR)/docker/rsync.done \
		$(BUILD_DIR)/docker/rabbitmq.done \
		$(BUILD_DIR)/docker/postgres.done \
		$(BUILD_DIR)/docker/rsyslog.done \
		$(BUILD_DIR)/docker/busybox.done
ifeq ($(DOCKER_PREBUILT),0)
	(cd $(BUILD_DIR)/docker/containers && tar cf fuel-images.tar *.tar)
	lrzip -L2 -U -D -f $(BUILD_DIR)/docker/containers/fuel-images.tar -o $(BUILD_DIR)/docker/fuel-images.tar.lrz
	rm -f $(BUILD_DIR)/docker/*tar
else
	rm -f $(BUILD_DIR)/docker/fuel-images.tar.lrz
ifeq ($(wildcard $(DOCKER_PREBUILT_SOURCE)),)
	wget -O $(BUILD_DIR)/docker/fuel-images.tar.lrz "$(DOCKER_PREBUILT_SOURCE)"
else
	cp $(DOCKER_PREBUILT_SOURCE) $(BUILD_DIR)/docker/fuel-images.tar.lrz
endif
endif
	mkdir -p $(BUILD_DIR)/docker/sources
	cp -r $(SOURCE_DIR)/docker/storage-* $(BUILD_DIR)/docker/sources/
	$(ACTION.TOUCH)

$(eval $(call build_container,astute))
$(eval $(call build_container,cobbler))
$(eval $(call build_container,mcollective))
$(eval $(call build_container,nailgun))
$(eval $(call build_container,nginx))
$(eval $(call build_container,ostf))
$(eval $(call build_container,rsync))
$(eval $(call build_container,rabbitmq))
$(eval $(call build_container,postgres))
$(eval $(call build_container,rsyslog))

