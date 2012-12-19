
/:=$(BUILD_DIR)/gems/

$/astute-0.0.1.gem: astute/astute.gemspec \
	  $(call find-files,astute/bin) \
		$(call find-files,astute/lib) \
		$(call find-files,astute/spec)
	@mkdir -p $(@D)
	cd $(<D) && \
		gem build $(<F)
	mv $(<D)/astute-*.gem $@
