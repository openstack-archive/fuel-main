# fuel/astute

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache; \
    yum update -y; \
    echo ruby21-nailgun-mcagents sysstat | xargs -n1 yum install -y --quiet

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN puppet apply --detailed-exitcodes -d -v \
        /etc/puppet/modules/nailgun/examples/astute-only.pp; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=file:/var/www/nailgun/centos/x86_64\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

VOLUME /etc/astute
CMD /usr/local/bin/start.sh
