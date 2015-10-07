# fuel-cobbler
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 53 53/udp 67 67/udp 69/udp 80 443

VOLUME /etc/cobbler

CMD ["/usr/lib/systemd/systemd"]
