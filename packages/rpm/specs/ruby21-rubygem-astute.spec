# Generated from astute-0.0.1.gem by gem2rpm -*- rpm-spec -*-
%define rbname astute
%define version 0.0.2
%define release 9
%global gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%global geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define gembuilddir %{buildroot}%{gemdir}

Summary: Orchestrator for OpenStack deployment
Name: ruby21-rubygem-%{rbname}

Version: %{version}
Release: %{release}
Group: Development/Ruby
License: Distributable
URL: http://fuel.mirantis.com
Source0: %{rbname}-%{version}.gem
# Make sure the spec template is included in the SRPM
Source1: astute.conf
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: ruby >= 2.1
Requires: ruby21-rubygem-activesupport = 3.0.10
Requires: ruby21-rubygem-mcollective-client = 2.4.1
Requires: ruby21-rubygem-symboltable = 1.0.2
Requires: ruby21-rubygem-rest-client = 1.6.7
Requires: ruby21-rubygem-popen4 = 0.1.2
Requires: ruby21-rubygem-amqp = 0.9.10
Requires: ruby21-rubygem-raemon = 0.3.0
Requires: ruby21-rubygem-net-ssh = 2.8.0
Requires: ruby21-rubygem-net-ssh-gateway = 1.2.0
Requires: ruby21-rubygem-net-ssh-multi = 1.2.0
Requires: openssh-clients
BuildRequires: ruby >= 2.1
BuildArch: noarch
Provides: ruby21(Astute) = %{version}


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
mkdir -p %{buildroot}%{_bindir}
mv %{gembuilddir}/bin/* %{buildroot}%{_bindir}
rmdir %{gembuilddir}/bin

install -d -m 750 %{buildroot}%{_sysconfdir}/astute
install -p -D -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/astute/astute.conf
cat > %{buildroot}%{_bindir}/astuted <<EOF
#!/bin/bash
ruby -r 'rubygems' -e "gem 'astute', '>= 0'; load Gem.bin_path('astute', 'astuted', '>= 0')" -- \$@
EOF

install -d -m 755 %{buildroot}%{_localstatedir}/log/astute

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{gemdir}/gems/%{rbname}-%{version}/bin/*
%{gemdir}/gems/%{rbname}-%{version}/lib/*
%{gemdir}/gems/%{rbname}-%{version}/spec/*
%{gemdir}/gems/%{rbname}-%{version}/examples/*

%dir %attr(0750, naily, naily) %{_sysconfdir}/%{rbname}
%config(noreplace) %attr(0640, root, naily) %{_sysconfdir}/%{rbname}/astute.conf
%dir %attr(0755, naily, naily) %{_localstatedir}/log/%{rbname}
%config(noreplace) %{_bindir}/astuted

%doc %{gemdir}/doc/astute-0.0.2
%{gemdir}/cache/astute-0.0.2.gem
%{gemdir}/specifications/astute-0.0.2.gemspec

%changelog
