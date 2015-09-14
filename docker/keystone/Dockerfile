FROM fuel/centos

MAINTAINER Łukasz Oleś loles@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean expire-cache;yum update -y;echo fuel-release fuel-openstack-metadata | xargs -n1 yum install -y --quiet

ADD etc /etc

RUN export FACTER_fuel_production=docker-build; puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/keystone-only.pp; [[ $? == 0 || $? == 2 ]]

ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all

EXPOSE 35357
EXPOSE 5000

CMD ["/usr/local/bin/start.sh"]
