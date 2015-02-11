# fuel/astute
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean expire-cache ; yum update -y; yum --quiet install -y ruby21-nailgun-mcagents sysstat

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/astute-only.pp; [[ $? == 0 || $? == 2 ]]

RUN chmod +x /usr/local/bin/start.sh;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all

VOLUME /etc/astute
CMD /usr/local/bin/start.sh
