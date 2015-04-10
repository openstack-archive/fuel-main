%define name fuel
%define version 6.1.0
%define openstack_version 2014.2-6.1
%define release 1

Summary: Fuel for OpenStack
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://www.mirantis.com
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-bootstrap-image >= %{version}
Requires: fuel-docker-images >= %{version}
Requires: fuel-library-6.1 >= %{version}
Requires: fuelmenu >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-target-centos-image >= %{version}
Requires: nailgun-net-check >= %{version}
Requires: python-fuelclient >= %{version}
Requires: yum

%description
Fuel for OpenStack is a lifecycle management utility for 
managing OpenStack.

%prep
rm -rf %{name}
mkdir %{name}

%build

%install

cat > %{buildroot}/etc/yum.repos.d/<< EOF
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/%{openstack_version}/centos/x86_64
gpgcheck=0
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%config(noreplace) /etc/yum.repos.d/nailgun.repo
