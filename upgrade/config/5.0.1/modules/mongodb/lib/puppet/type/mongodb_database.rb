Puppet::Type.newtype(:mongodb_database) do
  @doc = "Manage MongoDB databases."

  ensurable

  newparam(:name, :namevar=>true) do
    desc "The name of the database."
    newvalues(/^\w+$/)
  end

  newparam(:admin_username) do
    desc "Administrator user login"
    defaultto 'admin'
  end

  newparam(:admin_password) do
    desc "Administrator user password"
  end

  newparam(:admin_host) do
    desc "Connect to this host as an admin user"
    defaultto 'localhost'
  end

  newparam(:admin_port) do
    desc "Connect to this port as an admin user"
    defaultto '27017'
  end

  newparam(:admin_database) do
    desc "Connect to this database as an admin user"
    defaultto 'admin'
  end

  newparam(:mongo_path) do
    desc "Path to mongo binary"
    defaultto '/usr/bin/mongo'
  end

  newparam(:tries) do
    desc "The maximum amount of two second tries to wait MongoDB startup."
    defaultto 10
    newvalues(/^\d+$/)
    munge do |value|
      Integer(value)
    end
  end

  autorequire(:package) do
    'mongodb'
  end

  autorequire(:service) do
    'mongodb'
  end
end
