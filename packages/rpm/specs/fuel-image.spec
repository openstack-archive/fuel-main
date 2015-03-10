%define name fuel-image
%define version 6.1.0
%define release 1

Summary: Fuel-image package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{name}-%{version}.tar.gz
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
rm -f build_ubuntu_image.py
rm -f create_separate_images.sh
tar -xzf %{SOURCE0}

%build

%install
cd $RPM_BUILD_DIR
install -p -D -m 755 build_ubuntu_image.py %{buildroot}%{_bindir}/build_ubuntu_image.py
install -p -D -m 755 create_separate_images.sh %{buildroot}%{_bindir}/create_separate_images.sh

%post
ln -s build_ubuntu_image.py %{_bindir}/fuel-image

%postun
rm -f %{_bindir}/fuel-image

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_bindir}/build_ubuntu_image.py
%{_bindir}/create_separate_images.sh
