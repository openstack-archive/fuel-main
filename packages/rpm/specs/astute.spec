%define rbname astute
%define version 6.0.0
%define release 1
%global gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%global geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define gembuilddir %{buildroot}%{gemdir}

Summary: Orchestrator for OpenStack deployment
Name: ruby21-rubygem-astute
Version: %{version}
Release: %{release}
Group: Development/Ruby
License: Distributable
URL: http://fuel.mirantis.com
Source0: %{rbname}-%{version}.tar.gz
# Make sure the spec template is included in the SRPM
BuildRoot: %{_tmppath}/%{rbname}-%{version}-root
Requires: ruby >= 2.1
Requires: ruby21-rubygem-activesupport = 3.0.10
Requires: ruby21-rubygem-mcollective-client = 2.4.1
Requires: ruby21-rubygem-symboltable = 1.0.2
Requires: ruby21-rubygem-rest-client = 1.6.7
Requires: ruby21-rubygem-popen4 = 0.1.2
Requires: ruby21-rubygem-amqp = 1.4.1
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
%setup -cq -n %{rbname}-%{version}

%build
cd %{_builddir}/%{rbname}-%{version}/ && gem build *.gemspec

%install
mkdir -p %{gembuilddir}
gem install --local --install-dir %{gembuilddir} --force %{_builddir}/%{rbname}-%{version}/%{rbname}-%{version}.gem
mkdir -p %{buildroot}%{_bindir}
mv %{gembuilddir}/bin/* %{buildroot}%{_bindir}
rmdir %{gembuilddir}/bin
install -d -m 750 %{buildroot}%{_sysconfdir}/astute
cat > %{buildroot}%{_bindir}/astuted <<EOF
#!/bin/bash
ruby -r 'rubygems' -e "gem 'astute', '>= 0'; load Gem.bin_path('astute', 'astuted', '>= 0')" -- \$@
EOF
install -d -m 755 %{buildroot}%{_localstatedir}/log/astute
#nailgun-mcagents
mkdir -p %{buildroot}/usr/libexec/mcollective/mcollective/agent/
cp -rf %{_builddir}/%{rbname}-%{version}/mcagents/* %{buildroot}/usr/libexec/mcollective/mcollective/agent/

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
%{gemdir}/gems/%{rbname}-%{version}/bin/*
%{gemdir}/gems/%{rbname}-%{version}/lib/*
%{gemdir}/gems/%{rbname}-%{version}/spec/*
%{gemdir}/gems/%{rbname}-%{version}/examples/*

%dir %attr(0750, naily, naily) %{_sysconfdir}/%{rbname}
%dir %attr(0755, naily, naily) %{_localstatedir}/log/%{rbname}
%config(noreplace) %{_bindir}/astuted

%doc %{gemdir}/doc/%{rbname}-%{version}
%{gemdir}/specifications/%{rbname}-%{version}.gemspec


%package -n ruby21-nailgun-mcagents

Summary:   MCollective Agents
Version:   %{version}
Release:   %{release}
License:   GPLv2
Requires:  ruby21-mcollective >= 2.2
URL:       http://mirantis.com

%description -n ruby21-nailgun-mcagents
MCollective agents

%files -n ruby21-nailgun-mcagents
/usr/libexec/mcollective/mcollective/agent/*

%package -n nailgun-mcagents

Summary:   MCollective Agents
Version:   %{version}
Release:   %{release}
License:   GPLv2
Requires:  mcollective >= 2.2
URL:       http://mirantis.com

%description -n nailgun-mcagents
MCollective agents

%files -n nailgun-mcagents
/usr/libexec/mcollective/mcollective/agent/*
