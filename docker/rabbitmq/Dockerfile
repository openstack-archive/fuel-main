# fuel/rabbitmq

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh
RUN systemctl mask firewalld.service

EXPOSE 4369 5672 15672 61613

CMD ["/usr/lib/systemd/systemd"]
