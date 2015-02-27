#fuel/centos-docker-build
FROM centos:centos6

MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN rm -f /etc/yum.repos.d/*;echo -e "[nailgun]\nname=Nailgun Local Repo\nbaseurl=file:///repo/os/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/nailgun.repo 
ADD start.sh /usr/local/bin/
ADD fuel-centos.ks /root/fuel-centos.ks
RUN chmod +x /usr/local/bin/start.sh
RUN touch /etc/sysconfig/network

CMD ["/usr/local/bin/start.sh"]
