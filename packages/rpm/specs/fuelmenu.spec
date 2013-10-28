%define name fuelmenu
%define version 0.1
%define unmangled_version 0.1
%define release 1

Summary: Console utility for pre-configuration of Fuel server
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Matthew Mosesohn <mmosesohn@mirantis.com>
Requires: bind-utils
Requires: dhcp_checker
Requires: nailgun-net-check
Requires: ntp
Requires: python-setuptools
Requires: python-netaddr
Requires: python-netifaces
Requires: python-urwid >= 1.1.0
Requires: PyYAML
Requires: python-ordereddict

%description
Summary: Console utility for pre-configuration of Fuel server

%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/etc
install -m 0600 fuelmenu/naily.facts.default $RPM_BUILD_ROOT/etc/naily.facts.default
install -m 0600 fuelmenu/naily.facts.default $RPM_BUILD_ROOT/etc/naily.facts
install -m 0600 fuelmenu/settings.yaml $RPM_BUILD_ROOT/etc/astute.yaml
%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%config /etc/naily.facts.default
%config(noreplace) /etc/naily.facts
%config(noreplace) /etc/astute.yaml
