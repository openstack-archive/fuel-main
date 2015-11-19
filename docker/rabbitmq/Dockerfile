# fuel/rabbitmq

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_
ENV EXTRA_RPM_REPOS _EXTRA_RPM_REPOS_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 4369 5672 15672 61613

CMD ["/usr/sbin/init"]
