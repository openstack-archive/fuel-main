#fuel/rabbitmq

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; yum --quiet install -y rabbitmq-server

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN mkdir -p /var/lib/hiera /var/log/rabbitmq; touch /var/lib/hiera/common.yaml;puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp; [ $? -lt 4 ]


RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; chmod +x /usr/local/bin/start.sh

EXPOSE 4369 5672 15672 61613
CMD ["/usr/local/bin/start.sh"]
