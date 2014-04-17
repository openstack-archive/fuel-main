# fuel-rsync
#
# Version     0.1

FROM centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

RUN yum -v install -y yum-utils
RUN yum --quiet install -y xinetd rsync

ADD etc /etc
RUN puppet apply -v /etc/puppet/modules/nailgun/examples/puppetsync-only.pp

RUN mkdir -p /usr/local/bin
ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 873
CMD /usr/local/bin/start.sh
