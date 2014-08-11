#fuel/centos-docker-build
FROM centos:centos6

MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo;yum clean all;yum --quiet install -y sudo

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh
ADD fuel-centos.ks /root

RUN sed -i '/requiretty/s/^/#/g' /etc/sudoers;touch /etc/sysconfig/network;mkdir -p /var/lib/hiera && touch /var/lib/hiera/common.yaml

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo;yum clean all;chmod +x /usr/local/bin/start.sh

CMD ["/usr/local/bin/start.sh"]
