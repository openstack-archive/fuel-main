FROM centos

MAINTAINER Aleksandr Didenko adidenko@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(/sbin/ip route | awk '/default/ { print $3 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet anacron rsyslog

ADD etc /etc

# let's disable some services and commands since we don't need them in our container
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/rsyslog
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/iptables
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /sbin/iptables

RUN chmod +x /etc/init.d/iptables /sbin/iptables /etc/init.d/rsyslog
RUN touch /etc/puppet/hiera.yaml

RUN /usr/bin/puppet apply -d -v /etc/puppet/modules/nailgun/examples/rsyslog-only.pp

ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all

EXPOSE 514
EXPOSE 514/udp

CMD ["/usr/local/bin/start.sh"]
