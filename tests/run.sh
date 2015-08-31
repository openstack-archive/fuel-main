apt-get install -qq -y unzip wget 2>&1 > /dev/null
cd /tmp && wget -q https://github.com/sstephenson/bats/archive/master.zip && unzip -qq master.zip && cd bats-master/ && ./install.sh /usr/local >/dev/null
cd /etc/iso/tests
bats test.sh
