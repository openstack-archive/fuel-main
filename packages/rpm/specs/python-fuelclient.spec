%define name python-fuelclient
%define unmangled_name fuelclient
%define version 0.2
%define release 3

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
BuildRequires:  python-setuptools
Requires: PyYAML
Requires: python-keystoneclient >= 1:0.4.1

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
