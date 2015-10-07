# fuel-nginx

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh
RUN systemctl mask firewalld.service

EXPOSE 8000 8080

CMD ["/usr/lib/systemd/systemd"]
