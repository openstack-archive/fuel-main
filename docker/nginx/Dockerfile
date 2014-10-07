#fuel-nginx

FROM fuel/centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -rf /etc/yum.repos.d/*; echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(route -n | awk '/^0.0.0.0/ { print $2 }'):_PORT_/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all

ADD etc /etc
ADD start.sh /usr/local/bin/start.sh

RUN mkdir -p /var/www/nailgun;chmod 755 /var/www/nailgun
RUN puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/nginx-only.pp; [ $? -lt 4 ]


RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:/var/www/nailgun/centos/x86_64\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo; yum clean all; chmod +x /usr/local/bin/start.sh

EXPOSE 8000 8080
CMD ["/usr/local/bin/start.sh"]

