Puppet::Type.type(:mongodb_user).provide(:mongodb) do
  require File.join(File.dirname(__FILE__), '..', 'common.rb')
  desc "Manage users for a MongoDB database."
  defaultfor :kernel => 'Linux'
  include MongoCommon

  def create
    Puppet.debug "mongodb_user: #{@resource[:name]} database '#{@resource[:database]}' create"
    mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.insert({user:'#{@resource[:name]}', pwd:'#{@resource[:password_hash]}', roles: #{@resource[:roles].inspect}})")
  end

  def destroy
    Puppet.debug "mongodb_user: #{@resource[:name]} database '#{@resource[:database]}' destroy"
    mongo("db.getMongo().getDB('#{@resource[:database]}').removeUser('#{@resource[:name]}')")
  end

  def exists?
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' exists?"
    block_until_mongodb(@resource[:tries])
    exists = mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.find({user:'#{@resource[:name]}'}).count()").strip.to_i > 0
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' exists? #{exists}"
    exists
  end

  def password_hash
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' password_hash get"
    hash = mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.findOne({user:'#{@resource[:name]}'})['pwd']").strip
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' password_hash: #{hash}"
    hash
  end

  def password_hash=(value)
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' password_hash set #{value.inspect}"
    mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.update({user:'#{@resource[:name]}'}, { $set: {pwd:'#{value}'}})")
  end

  def roles
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' roles get"
    roles = mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.findOne({user:'#{@resource[:name]}'})['roles']").strip.split(',').sort
    Puppet.debug "mongodb_user: '#{@resource[:name]}' roles: #{roles.inspect}"
    roles
  end

  def roles=(value)
    Puppet.debug "mongodb_user: '#{@resource[:name]}' database '#{@resource[:database]}' roles set #{value.inspect}"
    mongo("db.getMongo().getDB('#{@resource[:database]}').system.users.update({user:'#{@resource[:name]}'}, { $set: {roles: #{@resource[:roles].inspect}}})")
  end

end
