%define name Shotgun
%define version 0.1.0
%define release 1

Summary: Shotgun package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  python-setuptools
BuildArch: noarch

Requires:    python-fabric == 1.7.0

%description
Shotgun package

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

