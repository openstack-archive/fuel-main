%define name fuel-package-updates
%define unmangled_name fuel_package_updates
%define version 6.0.0
%define release 1

Summary: Fuel package update downloader
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{unmangled_name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  python-setuptools
BuildArch: noarch

Requires:    python-keystoneclient >= 0.11
Requires:    python-keystonemiddleware >= 1.2.0
Requires:    python-ordereddict >= 1.1

%description
Command line utility to download apt/yum repositories for Fuel

%prep
%setup -n %{unmangled_name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(0755,root,root)
