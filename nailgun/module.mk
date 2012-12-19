/:=$(BUILD_DIR)/nailgun/

%: /:=$/

$/Nailgun-$(NAILGUN_VERSION).tar.gz: \
	 $(call find-files,nailgun)
	cd nailgun && \
	python setup.py sdist --dist-dir $/

test-unit: test-unit-nailgun

.PHONY: test-unit-nailgun
test-unit-nailgun:
	cd nailgun && ./run_tests.sh
