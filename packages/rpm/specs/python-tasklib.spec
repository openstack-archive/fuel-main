%define name python-tasklib
%define unmangled_name tasklib
%define version 0.1
%define release 1

Name:      %{name}
Summary:   Fuel tasklib
Version:   %{version}
Release:   %{release}
License:   GPLv2
Source0:   %{unmangled_name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:       http://github.com/Mirantis

BuildRequires:  python-setuptools

Requires: python-argparse
Requires: python-daemonize
Requires: python-yaml


%description
Medium between configuration management providers and user.
For plagability, control and simple interface.

%prep
%setup -n %{unmangled_name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
