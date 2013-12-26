.PHONY: repos

repos: $(BUILD_DIR)/repos/repos.done

$(BUILD_DIR)/repos/repos.done:
	sed -i '/^  fuelmain_sha:/d' $(BUILD_DIR)/repos/version.yaml
	/bin/echo "  fuelmain_sha: \"`git rev-parse --verify HEAD`\"" >> $(BUILD_DIR)/repos/version.yaml
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
	# Clone with depth=1 if no gerrit commits given, otherwise clone everything
	test "$5" = "none" && git clone --depth 1 --branch $3 $2 $(BUILD_DIR)/repos/$1 || git clone --branch $3 $2 $(BUILD_DIR)/repos/$1
	# Pull gerrit commits if given
	$(foreach var,$5,
		test "$(var)" = "none" || ( cd $(BUILD_DIR)/repos/$1 && git fetch $4 $(var) && git cherry-pick FETCH_HEAD ) ;
	)
	# Update versions.yaml
	touch $(BUILD_DIR)/repos/version.yaml
	sed -i '/^  $1_sha:/d' $(BUILD_DIR)/repos/version.yaml
	/bin/echo "  $1_sha: \"`cd $(BUILD_DIR)/repos/$1 && git rev-parse --verify HEAD`\"" >> $(BUILD_DIR)/repos/version.yaml
	touch $(BUILD_DIR)/repos/$1.done
endef

$(eval $(call build_repo,nailgun,$(NAILGUN_REPO),$(NAILGUN_COMMIT),$(NAILGUN_GERRIT_URL),$(NAILGUN_GERRIT_COMMIT)))
$(eval $(call build_repo,astute,$(ASTUTE_REPO),$(ASTUTE_COMMIT),$(ASTUTE_GERRIT_URL),$(ASTUTE_GERRIT_COMMIT)))
$(eval $(call build_repo,fuellib,$(FUELLIB_REPO),$(FUELLIB_COMMIT),$(FUELLIB_GERRIT_URL),$(FUELLIB_GERRIT_COMMIT)))
$(eval $(call build_repo,ostf,$(OSTF_REPO),$(OSTF_COMMIT),$(OSTF_GERRIT_URL),$(OSTF_GERRIT_COMMIT)))
