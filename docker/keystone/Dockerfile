# fuel/keystone

FROM fuel/centos
MAINTAINER Łukasz Oleś loles@mirantis.com

WORKDIR /root

ENV container docker
ENV DOCKER_PORT _PORT_
ENV EXTRA_RPM_REPOS _EXTRA_RPM_REPOS_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 35357 5000

CMD ["/usr/sbin/init"]
