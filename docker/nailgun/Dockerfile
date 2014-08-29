# fuel-nailgun
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo;yum clean all;mkdir -p /opt/gateone/users/ANONYMOUS/ /var/log/nailgun

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

#FIXME(mattymo): waiting for https://bugs.launchpad.net/fuel/+bug/1363085
RUN yum install -y python-pbr python-lxml

RUN puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp; [ $? -lt 4 ]
RUN mkdir -p /var/log/remote /var/www/nailgun

#clean everything up
RUN yum --quiet remove -y gcc-c++ --skip-broken

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; chmod +x /usr/local/bin/start.sh

EXPOSE 8001
VOLUME ["/usr/share/nailgun/static", "/etc/nailgun"]
CMD /usr/local/bin/start.sh
