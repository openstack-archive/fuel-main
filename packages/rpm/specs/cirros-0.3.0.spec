Name:      cirros-uec
Summary:   CirrOS is a Tiny OS that specializes in running on a cloud
Version:   0.3.0
Release:   1
License:   GPLv2
Source0:   https://launchpad.net/cirros/trunk/0.3.0/+download/cirros-%{version}-x86_64-uec.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       https://launchpad.net/cirros
%description
This is a project to build a small cloud image that has useful tools and
function for debugging or developing cloud infrastructure.

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
tar zxf %{_sourcedir}/cirros-%{version}-x86_64-uec.tar.gz -C %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/opt/nailgun/artifacts
install -m 644 cirros-%{version}-x86_64-blank.img %{buildroot}/opt/nailgun/artifacts/cirros-%{version}-x86_64-blank.img
install -m 644 cirros-%{version}-x86_64-vmlinuz %{buildroot}/opt/nailgun/artifacts/cirros-%{version}-x86_64-vmlinuz
install -m 644 cirros-%{version}-x86_64-initrd %{buildroot}/opt/nailgun/artifacts/cirros-%{version}-x86_64-initrd

%clean
rm -rf %{buildroot}

%files
/opt/nailgun/artifacts/cirros-%{version}-x86_64-blank.img
/opt/nailgun/artifacts/cirros-%{version}-x86_64-vmlinuz
/opt/nailgun/artifacts/cirros-%{version}-x86_64-initrd
