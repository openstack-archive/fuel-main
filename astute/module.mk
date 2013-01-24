ASTUTE_VERSION:=$(shell ruby -e "require '$(SOURCE_DIR)/astute/lib/astute/version.rb'; puts Astute::VERSION")

$(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem: \
		$(SOURCE_DIR)/astute/astute.gemspec \
		$(call find-files,astute/bin) \
		$(call find-files,astute/lib) \
		$(call find-files,astute/spec)
	@mkdir -p $(@D)
	cd $(SOURCE_DIR)/astute && gem build astute.gemspec
	mv $(SOURCE_DIR)/astute/astute-$(ASTUTE_VERSION).gem $@
