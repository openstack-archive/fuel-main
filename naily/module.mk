
/:=$(BUILD_DIR)/gems/

$/naily-0.0.1.gem: naily/naily.gemspec \
	  $(addprefix naily/bin/,$(call find-files,naily/bin)) \
		$(addprefix naily/lib/,$(call find-files,naily/lib))
	@mkdir -p $(@D)
	cd $(<D) && \
		gem build $(<F)
	mv $(<D)/naily-*.gem $@
