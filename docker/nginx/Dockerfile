#Should be linked to the following
# -volumes-from nailgun
# -volumes-from storage-dump
# --volume "/etc/fuel:/etc/fuel"

FROM centos
MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

WORKDIR /root

RUN rm -rf /etc/yum.repos.d/*
RUN echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=http://$(/sbin/ip route | awk '/default/ { print $3 }'):8080/centos/fuelweb/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo
RUN yum clean all
RUN yum --quiet install -y ruby21-puppet
RUN yum --quiet -y install nginx

ADD etc /etc
ADD site.pp /root/site.pp
RUN mkdir -p /var/www/nailgun
RUN chmod 755 /var/www/nailgun
RUN puppet apply -v /etc/puppet/modules/nailgun/examples/nginx-only.pp

RUN mkdir -p /usr/local/bin
ADD start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 8000
EXPOSE 8080
CMD ["/usr/local/bin/start.sh"]

