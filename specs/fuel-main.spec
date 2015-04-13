#TEMP fixme 
%define repo_name fuel-main

%define name fuel-image
%define version 6.1.0
%define release 1

Summary: Fuel-image package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{repo_name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires: python-setuptools
BuildRequires: python-pbr
BuildArch: noarch

Requires:    python
Requires:    PyYAML
Requires:    python-argparse
Requires:    gzip
Requires:    bzip2
Requires:    debootstrap
Requires:    e2fsprogs
Requires:    util-linux-ng
Requires:    coreutils
Requires:    xz

%description
Fuel-image package

%prep
%setup -cq -n %{name}-%{version}
%build

%install
install -p -D -m 755 %{_builddir}/%{name}-%{version}/image/ubuntu/build_on_masternode/build_ubuntu_image.py %{buildroot}%{_bindir}/build_ubuntu_image.py
install -p -D -m 755 %{_builddir}/%{name}-%{version}/image/ubuntu/build_on_masternode/create_separate_images.sh %{buildroot}%{_bindir}/create_separate_images.sh

%post
ln -s %{_bindir}/build_ubuntu_image.py %{_bindir}/fuel-image

%postun
rm -f %{_bindir}/fuel-image

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_bindir}/build_ubuntu_image.py
%{_bindir}/create_separate_images.sh

%package -n fuel-release
Summary: Fuel for OpenStack
Version: %{version}
Release: %{release}
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-bootstrap-image >= %{version}
Requires: fuel-dockerctl >= 6.1
Requires: fuel-docker-images >= %{version}
Requires: fuel-library >= 6.1
Requires: fuelmenu >= %{version}
Requires: fuel-package-updates >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-target-centos-images >= %{version}
Requires: nailgun-net-check >= %{version}
Requires: python-fuelclient >= %{version}
Requires: yum

%description -n fuel-release
Fuel for OpenStack is a lifecycle management utility for 
managing OpenStack.

%files -n fuel-release
%defattr(-,root,root)
