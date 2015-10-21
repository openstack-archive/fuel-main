# fuel/mcollective

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache;

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN mkdir -p /var/lib/fuel/ibp; \
    /usr/bin/puppet apply --detailed-exitcodes -d -v \
        /etc/puppet/modules/nailgun/examples/mcollective-only.pp; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=file:/var/www/nailgun/centos/x86_64\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

CMD /usr/local/bin/start.sh
