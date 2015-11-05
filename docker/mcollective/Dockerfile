# fuel/mcollective

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/repo/os/x86_64/\n\
gpgcheck=0\n\
[mos]\n\
name=MOS Local Repo\n\
baseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/mos-repo/\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache; \
    yum update -y; \
    echo ruby21-mcollective shotgun fuel-agent fuel-provisioning-scripts daemonize \
        | xargs -n1 yum install -y --quiet

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

# TODO(bpiotrowski): remove old file path after new ISO is used on CI
RUN mkdir -p /var/lib/fuel/ibp; \
    if [[ -f /etc/puppet/modules/nailgun/examples/mcollective-only.pp ]]; then \
        /usr/bin/puppet apply --detailed-exitcodes -d -v \
            /etc/puppet/modules/nailgun/examples/mcollective-only.pp; \
    else \
        /usr/bin/puppet apply --detailed-exitcodes -d -v \
            /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp; \
    fi; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=file:/var/www/nailgun/centos/x86_64\n\
gpgcheck=0\n\
[mos]\n\
name=MOS Local Repo\n\
baseurl=file:/var/www/nailgun/mos-centos/x86_64\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

CMD /usr/local/bin/start.sh
