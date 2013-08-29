$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile: $(call depv,MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile:
	mkdir -p $(@D)
	echo -n > $@
	for i in $(MIRROR_GEMS); do \
		echo "source \"$$i\"" >> $@; \
	done

$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile: $(call depv,MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile: \
		$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile.lock \
		$(BUILD_DIR)/packages/gems/build.done \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/repos/nailgun.done
	echo -n > $@
	for i in $(MIRROR_GEMS); do \
		echo "source \"$$i\"" >> $@; \
	done
	echo "source \"file://$(BUILD_MIRROR_GEMS)\"" >> $@
	echo "gemspec :path => \"$(BUILD_DIR)/repos/nailgun/naily\"" >> $@
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile.lock: \
		$(BUILD_DIR)/repos/nailgun.done \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/naily/Gemfile.lock)
	mkdir -p $(@D)
	cp $(BUILD_DIR)/repos/nailgun/naily/Gemfile.lock $@

$(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done: \
		$(SOURCE_DIR)/requirements-gems.txt \
		$(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile \
		$(BUILD_DIR)/mirror/gems/gems-bundle/naily/Gemfile
	mkdir -p $(BUILD_DIR)/mirror/gems/gems-bundle
	cat $(SOURCE_DIR)/requirements-gems.txt | while read gem ver; do \
		echo "gem \"$${gem}\", \"$${ver}\"" >> $(BUILD_DIR)/mirror/gems/gems-bundle/Gemfile; \
	done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/gems-bundle.done: $(BUILD_DIR)/mirror/gems/gems-bundle-gemfile.done
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle && bundle install --path=. && bundle package )
	find $(BUILD_DIR)/mirror/gems/gems-bundle/naily \( -name "astute*.gem*" \) -exec rm '{}' \+
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle/naily && bundle install --path=. && bundle package )
	( cd $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/ && \
		gem fetch `for i in $(MIRROR_GEMS); do echo -n "--source $$i "; done` -v 1.3.4 bundler )
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/gems/build.done: $(call depv,LOCAL_MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/build.done: $(call depv,BUILD_MIRROR_GEMS)
$(BUILD_DIR)/mirror/gems/build.done: $(BUILD_DIR)/mirror/gems/gems-bundle.done
	@mkdir -p $(LOCAL_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/mirror/gems/gems-bundle/vendor/cache/*.gem $(LOCAL_MIRROR_GEMS)/gems
	find $(BUILD_DIR)/mirror/gems/gems-bundle/naily/vendor/cache/ \
		\( -name "*.gem" -a ! -name "astute*" -a ! -name "mcollective*" -a ! -name "raemon*" \) \
		-exec cp '{}' $(LOCAL_MIRROR_GEMS)/gems \;
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)
