Name:      fuel-ansible
Summary:   Ansible modules required by Fuel
Version:   0.1.0
Release:   1
License:   GPLv2
Source0:   fuel-ansible.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}
URL:       http://mirantis.com

BuildArch: noarch

Requires:  ansible >= 1.7.1

%description
Ansible modules for fuel

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
tar -xf %{SOURCE0} -C %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/usr/share/ansible
cp -rv * %{buildroot}/usr/share/ansible

%clean
rm -rf %{buildroot}

%files
%dir /usr/share/ansible
%dir /usr/share/ansible/*
/usr/share/ansible/*/*
