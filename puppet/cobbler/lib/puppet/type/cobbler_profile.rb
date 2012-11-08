require 'puppet'

Puppet::Type.newtype(:cobbler_profile) do

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

  newparam(:distro) do
    desc "Distro"
    newvalues(/^\S+$/)
  end

  newparam(:kopts) do
    desc "Kernel options"
    newvalues(/^.*$/)
  end

  newparam(:ksmeta) do
    desc "Kickstart metadata"
    newvalues(/^((\S+=\S+) +)*(\S+=\S+)*$/)
  end

  newparam(:menu) do
    desc "Include|Exclude this profile into boot menu"
    newvalues(:true, :false)
  end

  newparam(:kickstart) do
    desc "Path to kickstart file"
    newvalues(/^(\/[^\/]+)*$/)
  end

  newparam(:name, :namevar => true) do
    desc "Name of profile"
    newvalues(/^\S+$/)
  end

end
