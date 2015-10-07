# fuel/rabbitmq

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_
ENV RABBITMQ_NODENAME localhost

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD rabbitmq-server.sh /usr/local/bin/
ADD supervisord.conf /etc/supervisord.d/

RUN chmod +x /usr/local/bin/{rabbitmq-server,setup,start}.sh

EXPOSE 4369 5672 15672 61613

CMD ["/bin/bash", "-c", "set -e && /usr/bin/supervisord -n"]
