Puppet::Type.type(:mongodb_database).provide(:mongodb) do
  require File.join(File.dirname(__FILE__), '..', 'common.rb')
  desc "Manages MongoDB database."
  defaultfor :kernel => 'Linux'
  include MongoCommon

  def create
    Puppet.debug "mongo_database: #{@resource[:name]} create"
    mongo('db.dummyData.insert({"created_by_puppet": 1})', @resource[:name])
  end

  def destroy
    Puppet.debug "mongo_database: #{@resource[:name]} destroy"
    mongo('db.dropDatabase()', @resource[:name])
  end

  def exists?
    Puppet.debug "mongo_database: '#{@resource[:name]}' exists?"
    block_until_mongodb(@resource[:tries])
    current_databases = mongo('db.getMongo().getDBNames()').strip.split(',')
    exists = current_databases.include?(@resource[:name])
    Puppet.debug "mongo_database: '#{@resource[:name]}' all: #{current_databases.inspect} '#{@resource[:name]}' exists? #{exists}"
    exists
  end

end
