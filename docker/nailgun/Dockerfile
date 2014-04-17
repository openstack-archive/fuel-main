FROM centos

MAINTAINER Aleksandr Didenko adidenko@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(/sbin/ip route | awk '/default/ { print $3 }'):8080/centos/fuelweb/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet

ADD astute.yaml /etc/astute.yaml
RUN mkdir -p /etc/nailgun
ADD version.yaml /etc/nailgun/version.yaml

ADD etc /etc
RUN mkdir -p /var/lib/hiera && touch /var/lib/hiera/common.yaml
RUN /usr/bin/puppet apply -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp

ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 8001
VOLUME /usr/share/nailgun/static

CMD ["/usr/local/bin/start.sh"]
