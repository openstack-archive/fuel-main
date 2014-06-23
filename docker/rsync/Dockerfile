# fuel-rsync
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo;yum clean all;yum --quiet install -y ruby21-puppet xinetd rsync logrotate

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN puppet apply -v /etc/puppet/modules/nailgun/examples/puppetsync-only.pp


RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all;chmod +x /usr/local/bin/start.sh

EXPOSE 873
CMD /usr/local/bin/start.sh
