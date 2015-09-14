FROM fuel/centos

MAINTAINER Aleksandr Didenko adidenko@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean expire-cache; yum update -y; echo sudo fuel-release fuel-openstack-metadata ruby21-mcollective shotgun fuel-agent fuel-provisioning-scripts | xargs -n1 yum install -y --quiet

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

# /var/lib/fuel/ibp is a mount point for IBP host volume
RUN export FACTER_fuel_production=docker-build; mkdir -p /var/lib/hiera /var/lib/fuel/ibp && touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml; /usr/bin/puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp; [[ $? == 0 || $? == 2 ]]

#FIXME(mattymo): Workaround to make diagnostic snapshots work
RUN mkdir -p /opt/nailgun/bin /var/www/nailgun/dump; ln -s /usr/bin/nailgun_dump /opt/nailgun/bin/nailgun_dump

# let's disable some services and commands since we don't need them in our container
RUN echo -e '#!/bin/bash\n#chkconfig: 345 20 80\nexit 0' > /etc/init.d/mcollective

RUN chmod +x /usr/local/bin/start.sh; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all

CMD ["/usr/local/bin/start.sh"]
