# fuel-cobbler
#
# Version     0.1

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; yum --quiet install -y httpd cobbler dnsmasq xinetd tftp-server; ln -s /etc/dnsmasq.conf /etc/cobbler.dnsmasq.conf

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

#Workaround for dnsmasq startup and create blank SSH key during build
RUN echo -e "NETWORKING=yes\nHOSTNAME=$HOSTNAME" > /etc/sysconfig/network; mkdir -p /root/.ssh; chmod 700 /root/.ssh; touch /root/.ssh/id_rsa.pub; /etc/init.d/httpd start && puppet apply -v /etc/puppet/modules/nailgun/examples/cobbler-only.pp

RUN chmod +x /usr/local/bin/start.sh;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/fuelweb/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all

EXPOSE 53 53/udp 67 67/udp 69/udp 80 443
VOLUME /etc/cobbler
CMD /usr/local/bin/start.sh
