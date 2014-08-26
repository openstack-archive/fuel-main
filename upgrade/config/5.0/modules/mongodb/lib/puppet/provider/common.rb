module MongoCommon

  def mongo_local(cmd, database = @resource[:admin_database], username = @resource[:admin_username], password = @resource[:admin_password])
    mongo_cmd = [
        @resource[:mongo_path],
        '--quiet',
        '--eval',
        cmd,
        database,
    ]
    output = Puppet::Util::Execution.execute(mongo_cmd, :failonfail => false, :combine => false)
    rc = $?.exitstatus
    Puppet.debug "Local Mongo: #{cmd} -> #{rc}: #{output}"
    [output, rc]
  end

  def mongo_remote(cmd, database = @resource[:admin_database], username = @resource[:admin_username], password = @resource[:admin_password])
    mongo_cmd = [
        @resource[:mongo_path],
        '--username',
        username,
        '--password',
        password,
        '--host',
        @resource[:admin_host],
        '--port',
        @resource[:admin_port],
        '--quiet',
        '--eval',
        cmd,
        database,
    ]
    output = Puppet::Util::Execution.execute(mongo_cmd, :failonfail => false, :combine => false)
    rc = $?.exitstatus
    Puppet.debug "Remote Mongo: #{cmd} -> #{rc}: #{output}"
    [output, rc]
  end

  def mongo(cmd, database = @resource[:admin_database], username = @resource[:admin_username], password = @resource[:admin_password])
    output, rc = mongo_remote(cmd, database,username,password)
    return output if rc == 0
    output, rc = mongo_local(cmd, database,username,password)
    return output if rc == 0
    raise Puppet::ExecutionFailure, output
  end

  def block_until_mongodb(tries = 10)
    begin
      mongo('db.getMongo()')
    rescue => e
      debug('MongoDB server not ready, retrying')
      sleep 2
      if (tries -= 1) > 0
        retry
      else
        raise e
      end
    end
  end

end