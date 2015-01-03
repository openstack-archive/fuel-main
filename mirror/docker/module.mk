.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	for i in $(BUILD_DIR)/docker/run/*.lock; do \
		LOCKFILE=$(BUILD_DIR)/docker/run/$${i}; \
		PIDFILE=$(BUILD_DIR)/docker/run/$${i%%.lock}; \
		if ps -o args= -p `cat $${PIDFILE}`| grep --quiet simple_http_daemon; then \
			kill `cat $${PIDFILE}`; \
			sleep 1; \
		else \
			rm -f $${PIDFILE} $${LOCKFILE}; \
			continue; \
		fi; \
		if [ -f $${PIDFILE} ]; then \
			kill -9 `cat $${PIDFILE}`; \
			rm -f $${PIDFILE} $${LOCKFILE}; \
		fi \
	done
	timeout -k5 4 sudo docker ps && sudo docker rm -f `sudo docker ps -a | awk '/fuel/ {print $$1}'` || true
	timeout -k5 4 sudo docker images && sudo docker rmi -f `sudo docker images | awk '/fuel/ { print $$3; }'` || true

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
