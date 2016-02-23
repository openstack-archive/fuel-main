define ACTION.COPY
@mkdir -p $(@D)
cp $< $@
endef

define ACTION.TOUCH
@mkdir -p $(@D)
touch $@
endef
