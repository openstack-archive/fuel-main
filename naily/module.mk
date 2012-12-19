
/:=$(BUILD_DIR)/gems/

$/naily-0.0.1.gem: naily/naily.gemspec \
	  $(call find-files,naily/bin) \
		$(call find-files,naily/lib)
	@mkdir -p $(@D)
	cd $(<D) && \
		gem build $(<F)
	mv $(<D)/naily-*.gem $@
