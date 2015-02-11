Name:      fuel-docker-images
Summary:   Fuel Docker images
Version:   1.0
Release:   1
License:   Apache 2.0
BuildRoot: %{_tmppath}/%{name}-%{version}
Source0:   fuel-images.tar.lrz
URL:       http://mirantis.com
Requires:  docker-io
Requires:  lrzip
%description
Images for deploying Fuel for OpenStack Docker containers

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{SOURCE0} %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/var/www/nailgun/docker/images
install -m 644 %{SOURCE0} %{buildroot}/var/www/nailgun/docker/images/fuel-images.tar.lrz

%clean
rm -rf %{buildroot}

%files
/var/www/nailgun/docker/images/fuel-images.tar.lrz

