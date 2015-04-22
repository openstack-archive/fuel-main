%define name fuel-docker-images
%define version 6.1.0
%define release 1

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

%files
%defattr(-,root,root)
/var/www/nailgun/docker/images/fuel-images.tar.lrz
/var/www/nailgun/docker/sources/*
/var/www/nailgun/docker/utils/*

