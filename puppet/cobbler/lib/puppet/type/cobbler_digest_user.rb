require 'puppet'

Puppet::Type.newtype(:cobbler_digest_user) do

  desc = "Type to manage cobbler digest users (/etc/cobbler/users.digest)"

  ensurable do
    defaultto(:present)
    newvalue(:present) do
      provider.create
    end
    newvalue(:absent) do
      provider.destroy
    end
  end

  newparam(:password) do
    desc "User password"
    newvalues(/^.{6,}$/)
  end

  newparam(:name, :namevar => true) do
    desc "Name of user"
    newvalues(/^\S+$/)
  end

end
