
/:=$(BUILD_DIR)/gems/

$/astute-0.1.gem: astute/astute.gemspec \
	  $(addprefix astute/bin/,$(call find-files,astute/bin)) \
		$(addprefix astute/lib/,$(call find-files,astute/lib)) \
		$(addprefix astute/mcollective/,$(call find-files,astute/mcollective)) \
		$(addprefix astute/puppet/,$(call find-files,astute/puppet)) \
		$(addprefix astute/spec/,$(call find-files,astute/spec))
	@mkdir -p $(@D)
	cd $(<D) && \
		gem build $(<F)
	mv $(<D)/astute-*.gem $@
