%define name fuel-tasks-validator
%define unmangled_name fuel-tasks-validator
%define version 6.1.0
%define release 1

Summary: Utility to work with and validate granular deployment tasks
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
BuildRequires:  python-pbr

%description
Summary: Utility to work with and validate granular deployment tasks

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
