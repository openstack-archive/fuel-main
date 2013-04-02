Name:      rbenv-ruby-1.9.3-p392
Summary:   Ruby 1.9.3-p392 inside rbenv environment
Version:   0.0.1
Release:   1
License:   Ruby
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://mirantis.com
%description
Ruby 1.9.3-p392 inside rbenv environment

%prep
rm -rf "%{name}-%{version}"
mkdir %{name}-%{version}
cd %{name}-%{version}
unzip -q %{_sourcedir}/382db59cd0c16518d0cec0974e220a2c46aa7a25.zip
           mv -f rbenv-382db59cd0c16518d0cec0974e220a2c46aa7a25 rbenv
unzip -q %{_sourcedir}/1fb955eead087646f4d73ac36786432c380309a9.zip
      mv -f ruby-build-1fb955eead087646f4d73ac36786432c380309a9 ruby-build
ln -fs `pwd`/rbenv /opt

%build
cd %{name}-%{version}
echo "system" > rbenv/version
RUBY_BUILD_CACHE_PATH=%{_sourcedir} ruby-build/bin/ruby-build 1.9.3-p392 /opt/rbenv/versions/1.9.3-p392

%install
mkdir -p %{buildroot}/opt/
cp -r %{name}-%{version}/rbenv %{buildroot}/opt/

%clean
rm -rf "%{buildroot}"
rm -f "/opt/rbenv"

%files
/opt/rbenv
