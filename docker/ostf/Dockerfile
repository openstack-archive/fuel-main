# fuel/ostf
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo;yum clean all; yum --quiet install -y python-fuelclient supervisor postgresql-libs

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

#FIXME(mattymo): missing dependencies in saharaclient
#https://bugs.launchpad.net/fuel/+bug/1363088
#and keystoneclient https://bugs.launchpad.net/fuel/+bug/1363085
RUN yum install -y python-oslo-i18n python-pbr python-lxml
RUN puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/ostf-only.pp; [ $? -lt 4 ]


RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; chmod +x /usr/local/bin/start.sh

EXPOSE 8777
CMD /usr/local/bin/start.sh
