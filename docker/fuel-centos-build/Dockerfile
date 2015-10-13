#fuel/centos-docker-build
FROM centos:centos6

MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN echo -e "\
[nailgun]\n\
name=Nailgun Local Repo\n\
baseurl=file:///repo/os/x86_64/\n\
gpgcheck=0" \
        > /etc/yum.repos.d/nailgun.repo

ADD start.sh /usr/local/bin/
ADD fuel-centos.ks /root/fuel-centos.ks

RUN chmod +x /usr/local/bin/start.sh; \
    touch /etc/sysconfig/network

CMD /usr/local/bin/start.sh
