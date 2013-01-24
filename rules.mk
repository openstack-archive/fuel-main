define ACTION.COPY
@mkdir -p $(@D)
cp $< $@
endef

define ACTION.TOUCH
@mkdir -p $(@D)
touch $@
endef

define NEWLINE


endef

$(BUILD_DIR)/%/.dir:
	mkdir -p $(@D)
	@touch $@

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))
find-files=$(shell test -d $1 && find $1 -type f 2> /dev/null)