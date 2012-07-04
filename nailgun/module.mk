
test-unit: test-unit-nailgun

.PHONY: test-unit-nailgun
test-unit-nailgun:
	cd nailgun && ./run_tests.sh

