
.PHONY: all clean help prerequisites

help:
	@echo 'Available targets:'
	@echo '  all - build product'
	@echo '  prerequisites - install all external prerequisistes'

all:

clean:

include prerequisites.mk

