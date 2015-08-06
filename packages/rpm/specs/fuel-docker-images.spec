%define name fuel-docker-images
%{!?version: %define version 7.0.0}
%{!?release: %define release 2}

Name:    %{name}
Summary:  Fuel Docker images
Version: %{version}
Release: %{release}
License:   Apache 2.0
BuildRoot: %{_tmppath}/%{name}-%{version}
Source0:   fuel-images.tar.lrz
Source1:   fuel-images-sources.tar.gz
URL:       http://mirantis.com
Requires:  docker-io
Requires:  lrzip
%description
Images for deploying Fuel for OpenStack Docker containers

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{SOURCE0} %{name}-%{version}
tar xzvf %{SOURCE1} -C %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/var/www/nailgun/docker/{images,sources,utils}
install -m 644 %{SOURCE0} %{buildroot}/var/www/nailgun/docker/images/fuel-images.tar.lrz
cp -R sources %{buildroot}/var/www/nailgun/docker/
cp -R utils %{buildroot}/var/www/nailgun/docker/

%clean
rm -rf %{buildroot}

%post
rm -f /var/www/nailgun/docker/images/fuel-images.tar
lrzip -d -o /var/www/nailgun/docker/images/fuel-images.tar /var/www/nailgun/docker/images/fuel-images.tar.lrz
if [ "$1" = "2" ]; then
  #upgrade
  cp /etc/fuel/astute.yaml /etc/fuel/astute.yaml.bak
  dockerctl shell cobbler cat /etc/cobbler/dnsmasq.template /var/www/nailgun/docker/utils/extra_nets_from_cobbler.py > /etc/fuel/astute.yaml.tmp
  mv /etc/fuel/astute.yaml.tmp /etc/fuel/astute.yaml
fi

%files
%defattr(-,root,root)
/var/www/nailgun/docker/images/fuel-images.tar.lrz
/var/www/nailgun/docker/sources/*
/var/www/nailgun/docker/utils/*
