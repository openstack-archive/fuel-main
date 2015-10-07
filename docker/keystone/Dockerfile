# fuel/keystone

FROM fuel/centos
MAINTAINER Łukasz Oleś loles@mirantis.com

WORKDIR /root

ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 35357 5000

CMD ["/usr/lib/systemd/systemd"]
