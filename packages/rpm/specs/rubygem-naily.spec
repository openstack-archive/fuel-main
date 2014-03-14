%define rbname naily
%define version 0.1.0
%define release 1

Summary: Backend server for Nailgun
Name: rubygem-%{rbname}
Version: %{version}
Release: %{release}%{dist}
Group: Development/Ruby
License: Distributable
URL:
Source0: %{rbname}-%{version}.gem
BuildRoot: %{_tmppath}/%{name}-%{version}-root

Requires: ruby
Requires: rubygems >= 1.3.7
Requires: rubygem-amqp = 0.9.10
Requires: rubygem-astute
Requires: rubygem-json = 1.6.1
Requires: rubygem-raemon = 0.3.0
Requires: rubygem-symboltable = 1.0.2

BuildRequires: ruby
BuildRequires: rubygems >= 1.3.7

BuildArch: noarch
Provides: rubygem(naily) = %{version}

%define gemdir /usr/lib/ruby/gems/1.8
%define gembuilddir %{buildroot}%{gemdir}

%description
Nailgun deployment job server


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
%{_bindir}/nailyd
%{gemdir}/gems/%{rbname}-%{version}/bin/nailyd
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/worker.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/version.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/reporter.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/dispatcher.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/config.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/producer.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/server.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily/task_queue.rb
%{gemdir}/gems/%{rbname}-%{version}/lib/naily.rb


%doc %{gemdir}/doc/%{rbname}-%{version}
%{gemdir}/cache/%{rbname}-%{version}.gem
%{gemdir}/specifications/%{rbname}-%{version}.gemspec

%changelog
