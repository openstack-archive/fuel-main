# Generated from astute-6.0.0.gem by gem2rpm -*- rpm-spec -*-
%define rbname astute
%define version 6.0.0
%define release 1

Summary: Orchestrator for OpenStack deployment
Name: ruby-gems-%{rbname}

Version: %{version}
Release: %{release}
Group: Development/Ruby
License: Distributable
URL: 
Source0: %{rbname}-%{version}.gem
# Make sure the spec template is included in the SRPM
Source1: ruby-gems-%{rbname}.spec.in
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: ruby [""]
Requires: ruby-gems >= 2.2.2
Requires: ruby-gems-activesupport = 3.0.10
Requires: ruby-gems-mcollective-client => 2.4.1
Requires: ruby-gems-mcollective-client < 2.5
Requires: ruby-gems-symboltable = 1.0.2
Requires: ruby-gems-rest-client => 1.6.7
Requires: ruby-gems-rest-client < 1.7
Requires: ruby-gems-popen4 => 0.1.2
Requires: ruby-gems-popen4 < 0.2
Requires: ruby-gems-net-ssh-multi => 1.1
Requires: ruby-gems-net-ssh-multi < 2
Requires: ruby-gems-amqp = 1.4.1
Requires: ruby-gems-raemon = 0.3.0
Requires: ruby-gems-facter 
Requires: ruby-gems-rake = 10.0.4
Requires: ruby-gems-rspec = 2.13.0
Requires: ruby-gems-mocha = 0.13.3
Requires: ruby-gems-simplecov => 0.7.1
Requires: ruby-gems-simplecov < 0.8
Requires: ruby-gems-simplecov-rcov => 0.2.3
Requires: ruby-gems-simplecov-rcov < 0.3
BuildRequires: ruby [""]
BuildRequires: ruby-gems >= 2.2.2
BuildArch: noarch
Provides: ruby(Astute) = %{version}

%define gemdir /var/lib/gems/2.1.0
%define gembuilddir %{buildroot}%{gemdir}

%description
Deployment Orchestrator of Puppet via MCollective. Works as a library or from
CLI.


%prep
%setup -T -c

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{gembuilddir}
gem install --local --install-dir %{gembuilddir} --force %{SOURCE0}
mkdir -p %{buildroot}/%{_bindir}
mv %{gembuilddir}/bin/* %{buildroot}/%{_bindir}
rmdir %{gembuilddir}/bin

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{_bindir}/astuted
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/path
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/
%{gemdir}/gems/astute-6.0.0/


%doc %{gemdir}/doc/astute-6.0.0
%{gemdir}/cache/astute-6.0.0.gem
%{gemdir}/specifications/astute-6.0.0.gemspec

%changelog
