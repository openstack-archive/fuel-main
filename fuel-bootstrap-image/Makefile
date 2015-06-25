

VERSION?=6.1.0

top_srcdir:=$(shell pwd)
ubuntu_DATA:=$(shell cd $(top_srcdir) && find share -type f)
top_builddir?=$(shell pwd)
-include config.mk
PREFIX?=/usr

all:
	@echo nop

install:
	install -d -m 755 $(DESTDIR)$(PREFIX)/bin
	install -d -m 755 $(DESTDIR)$(PREFIX)/share/fuel-bootstrap-image
	install -m 755 -t $(DESTDIR)$(PREFIX)/bin $(top_srcdir)/bin/fuel-bootstrap-image
	tar cf - -C $(top_srcdir) share | tar xf - -C $(DESTDIR)$(PREFIX)

dist: $(top_builddir)/fuel-bootstrap-image-$(VERSION).tar.gz

$(top_builddir)/fuel-bootstrap-image-$(VERSION).tar.gz: STAGEDIR:=$(top_builddir)/dist/fuel-bootstrap-image
$(top_builddir)/fuel-bootstrap-image-$(VERSION).tar.gz: bin/fuel-bootstrap-image $(ubuntu_DATA) Makefile configure
	mkdir -p $(STAGEDIR)/share
	mkdir -p $(STAGEDIR)/bin
	tar cf - -C $(top_srcdir) bin share | tar xf - -C $(STAGEDIR)
	cp -a $(top_srcdir)/Makefile $(top_srcdir)/configure $(top_srcdir)/fuel-bootstrap-image.spec $(STAGEDIR)
	tar czf $@.tmp -C $(dir $(STAGEDIR)) $(notdir $(STAGEDIR))
	mv $@.tmp $@

rpm: SANDBOX:=$(top_builddir)/rpmbuild
rpm: $(top_builddir)/fuel-bootstrap-image-$(VERSION).tar.gz fuel-bootstrap-image.spec
	rm -rf $(SANDBOX)
	mkdir -p $(SANDBOX)/SOURCES $(SANDBOX)/SPECS $(SANDBOX)/tmp
	cp -a $< $(SANDBOX)/SOURCES
	cp -a $(top_srcdir)/fuel-bootstrap-image.spec $(SANDBOX)/SPECS
	fakeroot rpmbuild --nodeps \
		--define '_tmppath $(SANDBOX)/tmp' \
		--define '_topdir $(SANDBOX)' \
		--define 'version $(VERSION)' \
		-ba $(SANDBOX)/SPECS/fuel-bootstrap-image.spec

clean:
	-@rm -f $(top_builddir)/config.mk

distclean: clean
	-@rm -f $(top_builddir)/fuel-bootstrap-image-$(VERSION).tar.gz
	-@rm -rf $(top_builddir)/rpmbuild
	-@rm -rf $(top_builddir)/dist

.PHONY: all install dist clean rpm
