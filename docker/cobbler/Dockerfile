# fuel/cobbler

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

#Make empty SSH key (populated later during real deployment)
RUN rm -rf /etc/yum.repos.d/*; \
    echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean expire-cache; \
    yum update -y; \
    mkdir -p /var/log/nailgun /root/.ssh; \
    chmod 700 /root/.ssh; \
    touch /root/.ssh/id_rsa.pub; \
    chmod 600 /root/.ssh/id_rsa.pub
    ln -s /etc/dnsmasq.conf /etc/cobbler.dnsmasq.conf

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN echo -e "NETWORKING=yes\nHOSTNAME=$HOSTNAME" > /etc/sysconfig/network; \
    /etc/init.d/httpd start; \
    puppet apply --detailed-exitcodes -dv \
        /etc/puppet/modules/nailgun/examples/cobbler-only.pp; \
    [[ $? == 0 || $? == 2 ]]

RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo; \
    yum clean all; \
    chmod +x /usr/local/bin/start.sh

EXPOSE 53 53/udp 67 67/udp 69/udp 80 443
VOLUME /etc/cobbler
CMD /usr/local/bin/start.sh
