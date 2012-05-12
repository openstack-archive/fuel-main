
.PHONY: install-prerequisites install-redis-server install-python-packages

install-prerequisites: install-python-packages install-redis-server

install-redis-server:
	sudo apt-get install redis-server

install-python-packages:
	sudo pip install -r requirements.txt

