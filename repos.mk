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
	sed -i '/^$1_sha:/d' $(BUILD_DIR)/repos/version.yaml
	/bin/echo -n "$1_sha: " >> $(BUILD_DIR)/repos/version.yaml
	cd $(BUILD_DIR)/repos/$1 && git rev-parse --verify HEAD >> $(BUILD_DIR)/repos/version.yaml
	touch $(BUILD_DIR)/repos/$1.done
endef

$(BUILD_DIR)/repos/repos.done:
	$(ACTION.TOUCH)

$(eval $(call build_repo,astute,https://github.com/Mirantis/astute.git,master))
$(eval $(call build_repo,nailgun,https://github.com/Mirantis/fuelweb.git,master))
$(eval $(call build_repo,fuel,https://github.com/Mirantis/fuel.git,master))
$(eval $(call build_repo,ostf_tests,https://github.com/Mirantis/fuel-ostf-tests.git,master))
$(eval $(call build_repo,ostf_plugin,https://github.com/Mirantis/fuel-ostf-plugin.git,master))
