# fuel/ostf

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD setup.sh /usr/local/bin/
ADD start.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 8777

CMD ["/usr/sbin/init"]
