# fuel/astute
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/setup.sh; \
	chmod +x /usr/local/bin/start.sh

RUN rm -f /etc/env.vars || true; \
	echo "DOCKER_PORT=_PORT_" >> /etc/env.vars

VOLUME ["/etc/astute"]

CMD ["/usr/lib/systemd/systemd"]
