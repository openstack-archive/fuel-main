# fuel/keystone

FROM fuel/centos
MAINTAINER Łukasz Oleś loles@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache; \
    yum update -y

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN puppet apply --detailed-exitcodes -d -v \
        /etc/puppet/modules/nailgun/examples/keystone-only.pp; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

EXPOSE 35357 5000
CMD /usr/local/bin/start.sh
