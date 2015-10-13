# fuel-nailgun

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

#Make empty SSH key (populated later during real deployment)
RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache; \
    yum update -y; \
    mkdir -p /var/log/nailgun /root/.ssh; \
    chmod 700 /root/.ssh; \
    touch /root/.ssh/id_rsa.pub; \
    chmod 600 /root/.ssh/id_rsa.pub

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN mkdir -p /var/log/remote /var/www/nailgun; \
    puppet apply --detailed-exitcodes -d -v \
        /etc/puppet/modules/nailgun/examples/nailgun-only.pp; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=file:/var/www/nailgun/centos/x86_64\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

EXPOSE 8001
VOLUME ["/usr/share/nailgun/static", "/etc/nailgun"]
CMD /usr/local/bin/start.sh
