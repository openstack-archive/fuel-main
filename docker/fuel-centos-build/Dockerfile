#fuel/centos-docker-build
FROM centos:centos7

MAINTAINER Matthew Mosesohn mmosesohn@mirantis.com

ENV container docker
ENV EXTRA_RPM_REPOS _EXTRA_RPM_REPOS_

RUN echo _CENTOS_RELEASE_ > /etc/yum/vars/releasever
RUN yum --disablerepo=* --enablerepo=C7.1.1503-base --enablerepo=C7.1.1503-extras --enablerepo=C7.1.1503-updates -y update
RUN yum clean all
RUN yum --disablerepo=* --enablerepo=C7.1.1503-base --enablerepo=C7.1.1503-extras --enablerepo=C7.1.1503-updates -y install dbus

RUN systemctl mask dev-mqueue.mount dev-hugepages.mount \
    systemd-remount-fs.service sys-kernel-config.mount \
    sys-kernel-debug.mount sys-fs-fuse-connections.mount \
    display-manager.service graphical.target systemd-logind.service \
    firewalld.service

ADD dbus.service /etc/systemd/system/dbus.service
RUN systemctl enable dbus.service

RUN rm -f /etc/yum.repos.d/*

ADD start.sh /usr/local/bin/
ADD fuel-centos.ks /root/fuel-centos.ks

RUN chmod +x /usr/local/bin/start.sh

# Set default target
RUN systemctl set-default multi-user.target

CMD  ["/usr/lib/systemd/systemd"]
