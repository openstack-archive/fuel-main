.PHONY: docker

ISOROOT:=$(BUILD_DIR)/iso/isoroot

RANDOM_PORT:=$(shell shuf -i 9000-65000 -n 1)

docker: $(BUILD_DIR)/docker/build.done

define build_container
$(BUILD_DIR)/docker/$1.done: \
		$(BUILD_DIR)/docker/yum_http_repo.done \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/iso/isoroot-files.done
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
	cp $(BUILD_DIR)/repos/fuellib/deployment/puppet/nailgun/examples/$1-only.pp $(BUILD_DIR)/docker/$1/site.pp
	sudo docker build -t fuel/$1 $(BUILD_DIR)/docker/$1
	sudo docker save fuel/$1 > $(BUILD_DIR)/docker/containers/$1.tar
	$$(ACTION.TOUCH)
endef

# Lrzip all containers into single archive
$(BUILD_DIR)/docker/build.done: \
		$(BUILD_DIR)/docker/rabbitmq.done \
		$(BUILD_DIR)/docker/postgres.done \
		$(BUILD_DIR)/docker/rsyslog.done
	# FIXME: start simplehttp server with PID and kill via PID
	kill `ps afuxww | grep "SimpleHTTPServer.*$(RANDOM_PORT)" | grep -v grep | awk '{print $$2}'`
#	(cd $(BUILD_DIR)/docker/containers && tar cv *.tar | lrzip > $(BUILD_DIR)/docker/fuel-images.tar.lrz)
	$(ACTION.TOUCH)

$(BUILD_DIR)/docker/yum_http_repo.done: $(BUILD_DIR)/mirror/centos/build.done
	(cd $(LOCAL_MIRROR_CENTOS) && python -m SimpleHTTPServer $(RANDOM_PORT) &)
	$(ACTION.TOUCH)

# TODO: refactor all containers to make them build accroding to this scheme
#$(eval $(call build_container,astute))
#$(eval $(call build_container,cobbler))
#$(eval $(call build_container,mcollective))
#$(eval $(call build_container,nailgun))
#$(eval $(call build_container,nginx))
#$(eval $(call build_container,ostf))
#$(eval $(call build_container,rsync))
$(eval $(call build_container,rabbitmq))
$(eval $(call build_container,postgres))
$(eval $(call build_container,rsyslog))

