FROM centos

MAINTAINER Aleksandr Didenko adidenko@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(/sbin/ip route | awk '/default/ { print $3 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet sudo ruby21-mcollective

ADD etc /etc

RUN mkdir -p /var/lib/hiera && touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml
RUN /usr/bin/puppet apply -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp

#FIXME(mattymo): Workaround to make diagnostic snapshots work
RUN yum install -y nailgun Shotgun
RUN mkdir -p /opt/nailgun/bin; ln -s /usr/bin/nailgun_dump /opt/nailgun/bin/nailgun_dump

# let's disable some services and commands since we don't need them in our container
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/mcollective

ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh
RUN mkdir -p /var/www/nailgun/dump

CMD ["/usr/local/bin/start.sh"]
