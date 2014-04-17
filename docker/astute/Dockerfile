# fuel/astute
#
# Version     0.1

FROM centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(/sbin/ip route | awk '/default/ { print $3 }'):8080/centos/fuelweb/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet

ADD etc /etc
RUN puppet apply -d -v /etc/puppet/modules/nailgun/examples/astute-only.pp

RUN mkdir -p /usr/local/bin
ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

CMD /usr/local/bin/start.sh
