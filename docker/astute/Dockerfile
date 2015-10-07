# fuel/astute
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD setup-container.service /etc/systemd/system/
ADD start-container.service /etc/systemd/system/

RUN yum install -y --quiet nailgun-mcagents sysstat

VOLUME ["/etc/astute"]

CMD ["/usr/lib/systemd/systemd"]
