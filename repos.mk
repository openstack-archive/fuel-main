.PHONY: repos

repos: $(BUILD_DIR)/repos/repos.done

$(BUILD_DIR)/repos/repos.done:
	$(ACTION.TOUCH)

# Usage:
# (eval (call build_repo,repo_name,repo_uri,sha))
define build_repo
$(BUILD_DIR)/repos/$1/%: $(BUILD_DIR)/repos/$1.done
$(BUILD_DIR)/repos/repos.done: $(BUILD_DIR)/repos/$1.done

$(BUILD_DIR)/repos/$1.done:
	# Clone repo and checkout required commit
	mkdir -p $(BUILD_DIR)/repos
	rm -rf $(BUILD_DIR)/repos/$1
	git clone $2 $(BUILD_DIR)/repos/$1
	cd $(BUILD_DIR)/repos/$1 && git reset --hard $3
	# Update versions.yaml
	touch $(BUILD_DIR)/repos/version.yaml
	sed -i '/^  $1_sha:/d' $(BUILD_DIR)/repos/version.yaml
	/bin/echo -n "  $1_sha: " >> $(BUILD_DIR)/repos/version.yaml
	cd $(BUILD_DIR)/repos/$1 && git rev-parse --verify HEAD >> $(BUILD_DIR)/repos/version.yaml
	touch $(BUILD_DIR)/repos/$1.done
endef

$(eval $(call build_repo,nailgun,$(NAILGUN_REPO),$(NAILGUN_COMMIT)))
$(eval $(call build_repo,astute,$(ASTUTE_REPO),$(ASTUTE_COMMIT)))
$(eval $(call build_repo,fuellib,$(FUELLIB_REPO),$(FUELLIB_COMMIT)))
$(eval $(call build_repo,ostf_tests,$(OSTF_TESTS_REPO),$(OSTF_TESTS_COMMIT)))
$(eval $(call build_repo,ostf_plugin,$(OSTF_PLUGIN_REPO),$(OSTF_PLUGIN_COMMIT)))
