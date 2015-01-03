.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	for i in /tmp/simple_http_daemon/*.lock; do \
		LOCKFILE=$${i}; \
		PIDFILE=$${i%%.lock}; \
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
	sudo sh -c 'docker ps && docker rm -f `docker ps -a | awk "/fuel/ {print $$1}"` 2>/dev/null || true'
	sudo sh -c 'docker images && docker rmi -f `docker images | awk "/fuel/ { print $$3; }"` 2>/dev/null || true'

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
