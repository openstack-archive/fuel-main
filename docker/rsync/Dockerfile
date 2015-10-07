# fuel/rsync

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/setup.sh
RUN systemctl mask firewalld.service

EXPOSE 873

CMD ["/usr/lib/systemd/systemd"]
