# fuel-nailgun

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 8001

VOLUME ["/usr/share/nailgun/static", "/etc/nailgun"]

CMD ["/usr/lib/systemd/systemd"]
