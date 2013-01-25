$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile: \
		$(SOURCE_DIR)/config.mk
	mkdir -p $(@D)
	echo -n > $@
	for i in $(MIRROR_GEMS); do \
		echo "source \"$$i\"" >> $@; \
	done

$(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done: \
		requirements-gems.txt \
		$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile
	mkdir -p $(BUILD_DIR)/mirror/gems/gems-bundle
	cat requirements-gems.txt | while read gem ver; do \
		echo "gem \"$${gem}\", \"$${ver}\"" >> $(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile; \
	done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/gems-bundle.done: $(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle && bundle install --path ./ && bundle package )
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/ && gem fetch -v 1.2.1 bundler )
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/build.done: $(BUILD_DIR)/mirror/gems/gems-bundle.done
	@mkdir -p $(LOCAL_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/*.gem $(LOCAL_MIRROR_GEMS)/gems
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)
