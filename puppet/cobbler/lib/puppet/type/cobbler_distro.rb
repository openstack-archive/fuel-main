require 'puppet'

Puppet::Type.newtype(:cobbler_distro) do

  desc = "Type to manage cobbler distros"

  ensurable do
    defaultto(:present)
    newvalue(:present) do
      provider.create
    end
    newvalue(:absent) do
      provider.destroy
    end
  end

  newparam(:kernel) do
    desc "Path to kernel"
    newvalues(/^(\/[^\/]+)+$/)
  end

  newparam(:initrd) do
    desc "Path to initrd"
    newvalues(/^(\/[^\/]+)+$/)
  end

  newparam(:arch) do
    desc "Architecture"
    newvalues(/^(x86_64|i386)$/)
  end

  newparam(:ksmeta) do
    desc "Kickstart metadata"
    newvalues(/^((\S+=\S+) +)*(\S+=\S+)*$/)
  end

  newparam(:breed) do
    desc "Breed"
    newvalues(/^(redhat|ubuntu|debian|suse)$/)
  end

  newparam(:osversion) do
    desc "OS Version"
    newvalues(/^(rhel6|rhel5|precise|natty|squeeze|stable|other)$/)
  end

  newparam(:name, :namevar => true) do
    desc "Name of distro"
    newvalues(/^\S+$/)
  end

end
