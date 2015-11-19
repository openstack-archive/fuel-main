# fuel-nailgun

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

ENV container docker
ENV DOCKER_PORT _PORT_
ENV EXTRA_RPM_REPOS _EXTRA_RPM_REPOS_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 8001

VOLUME ["/usr/share/nailgun/static", "/etc/nailgun"]

CMD ["/usr/sbin/init"]
