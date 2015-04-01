%define name python-fuelclient
%define unmangled_name python-fuelclient
%define version 6.0.0
%define release 1

Summary: Console utility for working with fuel rest api
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{unmangled_name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
BuildRequires: python-setuptools

BuildRequires: python-pbr >= 0.6
BuildRequires: python-pbr != 0.7
BuildRequires: python-pbr < 1.0

Requires: python >= 2.6
Requires: python <= 2.7

Requires: python-argparse == 1.2.1

Requires: PyYAML >= 3.1.0
Requires: PyYAML <= 3.10

Requires: python-requests >= 2.1.0
Requires: python-requests <= 2.2.1

Requires: python-keystoneclient >= 0.10.0
Requires: python-keystoneclient <= 1.1.0

Requires: python-cliff >= 1.7.0
Requires: python-cliff <= 1.9.0

Requires: python-six >= 1.7.0
Requires: python-six <= 1.9.0

%description
Summary: Console utility for working with fuel rest api

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
