FROM fuel/centos

MAINTAINER Aleksandr Didenko adidenko@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all;yum --quiet install -y anacron rsyslog

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

# let's disable some services and commands since we don't need them in our container
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/rsyslog;echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/iptables;echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /sbin/iptables;chmod +x /etc/init.d/iptables /sbin/iptables /etc/init.d/rsyslog
RUN touch /etc/puppet/hiera.yaml;/usr/bin/puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/rsyslog-only.pp; [ $? -lt 4 ]
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all;chmod +x /usr/local/bin/start.sh

EXPOSE 514 514/udp
CMD ["/usr/local/bin/start.sh"]
