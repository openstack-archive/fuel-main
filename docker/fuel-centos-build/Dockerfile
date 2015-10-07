#fuel/centos-docker-build
FROM centos:centos7

MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

RUN yum -y update
RUN yum clean all
RUN yum -y install dbus

RUN systemctl mask dev-mqueue.mount dev-hugepages.mount \
    systemd-remount-fs.service sys-kernel-config.mount \
    sys-kernel-debug.mount sys-fs-fuse-connections.mount \
    display-manager.service graphical.target systemd-logind.service
ADD dbus.service /etc/systemd/system/dbus.service
RUN systemctl enable dbus.service

RUN rm -f /etc/yum.repos.d/*
ADD nailgun.repo /etc/yum.repos.d/

ADD start.sh /usr/local/bin/
ADD fuel-centos.ks /root/fuel-centos.ks

RUN chmod +x /usr/local/bin/start.sh

VOLUME ["/sys/fs/cgroup"]

CMD  ["/usr/lib/systemd/systemd"]
