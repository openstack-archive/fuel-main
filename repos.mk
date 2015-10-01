.PHONY: repos clean-repos

clean-repos:
	rm -rf $(BUILD_DIR)/repos

repos: $(BUILD_DIR)/repos/repos.done

fuel_components_repos:=
# Usage:
# (eval (call build_repo,repo_name,repo_uri,sha))
define build_repo
$(BUILD_DIR)/repos/$1/%: $(BUILD_DIR)/repos/$1.done
$(BUILD_DIR)/repos/repos.done: $(BUILD_DIR)/repos/$1.done
fuel_components_repos:=$(fuel_components_repos) $1

$(BUILD_DIR)/repos/$1.done:
	# Clone repo and checkout required commit
	mkdir -p $(BUILD_DIR)/repos
	rm -rf $(BUILD_DIR)/repos/$1

	#Clone everything and checkout to branch (or hash)
	git clone $2 $(BUILD_DIR)/repos/$1 && (cd $(BUILD_DIR)/repos/$1 && git checkout -q $3)

ifeq ($(strip $(GERRIT_BRANCH)),)
	# Pull gerrit commits if given
	$(foreach var,$(filter-out none,$5),
		( cd $(BUILD_DIR)/repos/$1 && git fetch $4 $(var) && git cherry-pick FETCH_HEAD ) ;
	)
	#FIXME(aglarendil): THIS IS A TEMPORARY FIX TO CHECK OUT CODE FOR PACKAGE BUILDING IN CI
	#IT SHOULD BE REPLACED WITH ANOTHER APPROACH SOON
else
	$(foreach var,$(filter-out none,$5),
	  ( cd $(BUILD_DIR)/repos/$1 && git fetch $4 $(var) && git checkout FETCH_HEAD ) ;
	)
endif

	touch $$@
endef


$(eval $(call build_repo,fuel-nailgun,$(NAILGUN_REPO),$(NAILGUN_COMMIT),$(NAILGUN_GERRIT_URL),$(NAILGUN_GERRIT_COMMIT)))
$(eval $(call build_repo,python-fuelclient,$(PYTHON_FUELCLIENT_REPO),$(PYTHON_FUELCLIENT_COMMIT),$(PYTHON_FUELCLIENT_GERRIT_URL),$(PYTHON_FUELCLIENT_GERRIT_COMMIT)))
$(eval $(call build_repo,fuel-agent,$(FUEL_AGENT_REPO),$(FUEL_AGENT_COMMIT),$(FUEL_AGENT_GERRIT_URL),$(FUEL_AGENT_GERRIT_COMMIT)))
$(eval $(call build_repo,fuel-nailgun-agent,$(FUEL_NAILGUN_AGENT_REPO),$(FUEL_NAILGUN_AGENT_COMMIT),$(FUEL_NAILGUN_AGENT_GERRIT_URL),$(FUEL_NAILGUN_AGENT_GERRIT_COMMIT)))
$(eval $(call build_repo,astute,$(ASTUTE_REPO),$(ASTUTE_COMMIT),$(ASTUTE_GERRIT_URL),$(ASTUTE_GERRIT_COMMIT)))
$(eval $(call build_repo,fuel-library,$(FUELLIB_REPO),$(FUELLIB_COMMIT),$(FUELLIB_GERRIT_URL),$(FUELLIB_GERRIT_COMMIT)))
$(eval $(call build_repo,fuel-ostf,$(OSTF_REPO),$(OSTF_COMMIT),$(OSTF_GERRIT_URL),$(OSTF_GERRIT_COMMIT)))
$(eval $(call build_repo,fuel-mirror,$(CREATEMIRROR_REPO),$(CREATEMIRROR_COMMIT),$(CREATEMIRROR_GERRIT_URL),$(CREATEMIRROR_GERRIT_COMMIT)))

$(BUILD_DIR)/repos/fuel-main.done:
	ln -s $(SOURCE_DIR) $(BUILD_DIR)/repos/fuel-main
	$(ACTION.TOUCH)
$(BUILD_DIR)/repos/repos.done: $(BUILD_DIR)/repos/fuel-main.done $(BUILD_DIR)/repos/fuel-library$(PRODUCT_VERSION).done

#FIXME(aglarendil): make repos generation uniform

$(BUILD_DIR)/repos/fuel-library$(PRODUCT_VERSION).done: $(BUILD_DIR)/repos/fuel-library.done
	ln -s $(BUILD_DIR)/repos/fuel-library $(BUILD_DIR)/repos/fuel-library$(PRODUCT_VERSION)
	$(ACTION.TOUCH)

$(BUILD_DIR)/repos/repos.done:
	version_yaml=$(BUILD_DIR)/repos/version.yaml; \
	for repo in $(strip $(fuel_components_repos)); do \
		repo_commit_id=`git --git-dir=$(BUILD_DIR)/repos/$$repo/.git rev-parse --verify HEAD`; \
		echo "  $${repo}_sha: \"$${repo_commit_id}\""; \
	done > $${version_yaml}.tmp; \
	fuelmain_commit_id=`git rev-parse --verify HEAD`; \
	echo "  fuelmain_sha: \"$${fuelmain_commit_id}\"" >> $${version_yaml}.tmp; \
	mv $${version_yaml}.tmp $${version_yaml}
	$(ACTION.TOUCH)
