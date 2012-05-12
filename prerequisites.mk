
prerequisites: install-python-packages install-redis-server

.PHONY: install-redis-server
install-redis-server:
	sudo apt-get install redis-server

.PHONY: install-python-packages
install-python-packages:
	sudo pip install -r requirements.txt

