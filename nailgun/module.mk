/:=$(BUILD_DIR)/nailgun/

%: /:=$/

sdist-nailgun:
	cd nailgun && \
	python setup.py sdist --dist-dir ../$/


test-unit: test-unit-nailgun

.PHONY: test-unit-nailgun sdist-nailgun
test-unit-nailgun:
	cd nailgun && ./run_tests.sh


