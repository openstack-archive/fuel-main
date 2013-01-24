NAILY_VERSION:=$(shell ruby -e "require '$(SOURCE_DIR)/naily/lib/naily/version.rb'; puts Naily::VERSION")

$(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem: \
		$(SOURCE_DIR)/naily/naily.gemspec \
		$(call find-files,$(SOURCE_DIR)/naily/bin) \
		$(call find-files,$(SOURCE_DIR)/naily/lib)
	@mkdir -p $(@D)
	cd $(SOURCE_DIR)/naily && gem build naily.gemspec
	mv $(SOURCE_DIR)/naily/naily-$(NAILY_VERSION).gem $@
