define ACTION.COPY
@mkdir -p $(@D)
cp $< $@
endef

define ACTION.TOUCH
@mkdir -p $(@D)
touch $@
endef

# This macros is to make targets dependent on variables
# It writes variable value into temporary file varname.tmp,
# then it compares temporary file with the varname.dep file.
# If there is a difference between them, varname.dep will be updated
# and the target which depends on it will be rebuilt.
# Example:
# target: $(call depv,varname)
DEPV_DIR:=$(BUILD_DIR)/depv
define depv
$(shell mkdir -p $(DEPV_DIR))
$(shell echo "$($1)" > $(DEPV_DIR)/$1.tmp)
$(shell diff >/dev/null 2>&1 $(DEPV_DIR)/$1.tmp $(DEPV_DIR)/$1.dep \
	|| mv $(DEPV_DIR)/$1.tmp $(DEPV_DIR)/$1.dep)
$(DEPV_DIR)/$1.dep
endef

define NEWLINE


endef

$(BUILD_DIR)/%/.dir:
	mkdir -p $(@D)
	@touch $@

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))
find-files=$(shell test -e $1 && find $1 -type f 2> /dev/null)

# uppercase conversion routine
# usage: UPPER_VAR = $(call uc,$(VAR)) 
uc = $(subst a,A,$(subst b,B,$(subst c,C,$(subst d,D,$(subst e,E,$(subst f,F,$(subst g,G,$(subst h,H,$(subst i,I,$(subst j,J,$(subst k,K,$(subst l,L,$(subst m,M,$(subst n,N,$(subst o,O,$(subst p,P,$(subst q,Q,$(subst r,R,$(subst s,S,$(subst t,T,$(subst u,U,$(subst v,V,$(subst w,W,$(subst x,X,$(subst y,Y,$(subst z,Z,$1))))))))))))))))))))))))))

comma:=,