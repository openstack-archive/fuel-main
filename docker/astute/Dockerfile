# fuel/astute

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh

VOLUME ["/etc/astute"]

CMD ["/usr/lib/systemd/systemd"]
