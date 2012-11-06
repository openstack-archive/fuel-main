/:=$(BUILD_DIR)/nailgun/

%: /:=$/

$/Nailgun-$(NAILGUN_VERSION).tar.gz:
	cd nailgun && \
	python setup.py sdist --dist-dir $/

test-unit: test-unit-nailgun

.PHONY: test-unit-nailgun $/Nailgun-$(NAILGUN_VERSION).tar.gz
test-unit-nailgun:
	cd nailgun && ./run_tests.sh
