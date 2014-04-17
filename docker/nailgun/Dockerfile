# fuel-nailgun
#
# Version     0.1

FROM centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet
RUN mkdir -p /opt/gateone/users/ANONYMOUS/
RUN mkdir -p /var/log/nailgun

ADD etc /etc

RUN puppet apply -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp

RUN mkdir -p /usr/local/bin /var/log/remote /var/www/nailgun
ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

#clean everything up
RUN yum --quiet remove -y gcc-c++ --skip-broken

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all

EXPOSE 8001
VOLUME /usr/share/nailgun/static
VOLUME /etc/nailgun
CMD /usr/local/bin/start.sh
