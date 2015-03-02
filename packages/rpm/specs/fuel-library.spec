Summary: Fuel-Library: a set of deployment manifests of Fuel for OpenStack 
Name: fuel-library-6.1
Version: 6.1
Release: 1
Group: System Environment/Libraries
License: GPLv2
URL: http://github.com/stackforge/fuel-library
Source0: %{name}-%{version}-%{release}.tar.gz
Provides: fuel-library
BuildArch: noarch
BuildRoot: %{_tmppath}/fuel-library-%{version}-%{release}


%description

Fuel is the Ultimate Do-it-Yourself Kit for OpenStack
Purpose built to assimilate the hard-won experience of our services team, it contains the tooling, information, and support you need to accelerate time to production with OpenStack cloud. OpenStack is a very versatile and flexible cloud management platform. By exposing its portfolio of cloud infrastructure services – compute, storage, networking and other core resources — through ReST APIs, it enables a wide range of control over these services, both from the perspective of an integrated Infrastructure as a Service (IaaS) controlled by applications, as well as automated manipulation of the infrastructure itself. This architectural flexibility doesn’t set itself up magically; it asks you, the user and cloud administrator, to organize and manage a large array of configuration options. Consequently, getting the most out of your OpenStack cloud over time – in terms of flexibility, scalability, and manageability – requires a thoughtful combination of automation and configuration choices.

This package contains deployment manifests and code to execute provisioning of master and slave nodes.

%prep
%setup -cq

%install
mkdir -p %{buildroot}/etc/puppet/2014.2-%{version}/modules/
cp -fr deployment/puppet/* %{buildroot}/etc/puppet/2014.2-%{version}/modules/

%files
/etc/puppet/2014.2-%{version}/modules/

%clean
rm -rf ${buildroot}

%changelog
* Tue Sep 10 2013 Vladimir Kuklin <vkuklin@mirantis.com> - 6.1
- Create spec
