# fuel/mcollective

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

WORKDIR /root

ENV container docker
ENV DOCKER_PORT _PORT_
ENV EXTRA_RPM_REPOS _EXTRA_RPM_REPOS_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/{setup,start}.sh

CMD ["/usr/sbin/init"]
