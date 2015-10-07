# fuel/rsyslog

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/setup.sh
RUN systemctl mask firewalld.service

EXPOSE 514 514/udp

CMD ["/usr/lib/systemd/systemd"]
