########################
# VBOX-SCRIPTS ARTIFACT
########################
vbox-scripts: $(VBOX_SCRIPTS_PATH)

$(VBOX_SCRIPTS_PATH): \
		$(call find-files,$(SOURCE_DIR)/virtualbox)
	mkdir -p $(@D)
	cd $(SOURCE_DIR) && zip -r $@ virtualbox
