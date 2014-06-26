.PHONY: docker

ISOROOT:=$(BUILD_DIR)/iso/isoroot
DOCKERROOT:=$(BUILD_DIR)/docker/dockerroot
DOCKER_LOGFILE:=$(BUILD_DIR)/docker/docker.log

RANDOM_PORT:=$(shell shuf -i 9000-65000 -n 1)

docker: $(BUILD_DIR)/docker/build.done \
        $(BuiLD_DIR)/docker/daemon-down.done

define build_container
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/iso/isoroot-files.done \
		$(BUILD_DIR)/docker/base-images.done \
                $(BUILD_DIR)/docker/daemon-up.done
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
	sudo docker $(DOCKER_OPTS) build -t fuel/$1_$(PRODUCT_VERSION) $(BUILD_DIR)/docker/$1
	kill `cat /tmp/simple_http_daemon_$(RANDOM_PORT).pid`
endif
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/docker/base-images.done: $(BUILD_DIR)/docker/daemon-up.done
	find $(LOCAL_MIRROR_DOCKER_BASEURL)/ -regex '.*xz' | xargs -n1 sudo docker $(DOCKER_OPTS) load -i
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/busybox.done: $(BUILD_DIR)/docker/daemon-up.done
	mkdir -p "$(BUILD_DIR)/docker/containers"
	touch "$(DOCKER_LOGFILE)"
	sudo DOCKER_LOGFILE="$(DOCKER_LOGFILE)" docker $(DOCKER_OPTS) save busybox > $(BUILD_DIR)/docker/containers/busybox.tar
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/daemon-up.done:
	mkdir -p "$(DOCKERROOT)"
	(sudo docker -d -g $(DOCKERROOT) -p $(BUILD_DIR)/docker/docker.pid -H=unix://$(BUILD_DIR)/docker/docker.sock -s="devicemapper" &)
	sleep 3
	$(ACTION.TOUCH)
$(BUILD_DIR)/docker/daemon-down.done:
	kill `cat $(BUILD_DIR)/docker/docker.pid`
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
	(cd $(DOCKERROOT) && sudo tar Scf $(BUILD_DIR)/docker/containers/fuel-images.tar *)
	lrzip -L2 -U -D -f $(BUILD_DIR)/docker/containers/fuel-images.tar -o $(BUILD_DIR)/docker/fuel-images.tar.lrz
	rm -f $(BUILD_DIR)/docker/containers/*tar
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

