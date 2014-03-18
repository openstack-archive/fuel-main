Name:      rbenv-ruby-1.9.3-p484
Summary:   Ruby 1.9.3-p484 inside rbenv environment
Version:   0.0.1
Release:   1
License:   Ruby
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://mirantis.com
%description
Ruby 1.9.3-p484 inside rbenv environment

%prep
rm -rf "%{name}-%{version}"
mkdir %{name}-%{version}
cd %{name}-%{version}
unzip -q %{_sourcedir}/382db59cd0c16518d0cec0974e220a2c46aa7a25.zip
           mv -f rbenv-382db59cd0c16518d0cec0974e220a2c46aa7a25 rbenv
unzip -q %{_sourcedir}/5ae03b839494d20435faad5bc31e2e95d10c4f33.zip
      mv -f ruby-build-5ae03b839494d20435faad5bc31e2e95d10c4f33 ruby-build
ln -fs `pwd`/rbenv /opt

%build
cd %{name}-%{version}
echo "system" > rbenv/version
RUBY_BUILD_CACHE_PATH=%{_sourcedir} ruby-build/bin/ruby-build 1.9.3-p484 /opt/rbenv/versions/1.9.3-p484

%install
mkdir -p %{buildroot}/opt/
cp -r %{name}-%{version}/rbenv %{buildroot}/opt/

%clean
rm -rf "%{buildroot}"
rm -f "/opt/rbenv"

%files
/opt/rbenv
