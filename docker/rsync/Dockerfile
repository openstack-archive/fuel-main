# fuel/rsync

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV container docker
ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD setup.sh /usr/local/bin/
ADD supervisord.conf /etc/supervisord.d/

RUN chmod +x /usr/local/bin/setup.sh

EXPOSE 873

CMD ["/usr/bin/supervisord", "-n"]
