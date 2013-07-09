require 'puppet'
Puppet::Type.type(:cobbler_digest_user).provide(:default) do

  defaultfor :operatingsystem => [:centos, :redhat, :debian, :ubuntu]

  # def self.instances
  #   list_users.each do |user, userhash|
  #     new(:name => user)
  #   end
  # end

  def create
    Puppet.info "cobbler_digest_user: updating user: #{@resource[:name]}"
    rm_user
    create_user
  end

  def destroy
    Puppet.info "cobbler_digest_user: removing user: #{@resource[:name]}"
    rm_user
  end

  def exists?
    users = list_users

    unless users[@resource[:name]]
      Puppet.info "cobbler_digest_user: user #{@resource[:name]} does not exist"
      return false
    end

    if hashline == users[@resource[:name]]
      Puppet.info "cobbler_digest_user: user #{@resource[:name]} already exists"
      return true
    end

    return false
  end

  private
  
  def hashline
    return `printf "#{@resource[:name]}:Cobbler:#{@resource[:password]}" | md5sum | awk '{print $1}'`.chomp
  end
  
  def list_users
    users = {}
    File.open("/etc/cobbler/users.digest", "r") do |file|
      while line = file.gets
        user, servicename, userhash = line.split(/:/)
        users[user] = userhash.chomp
      end
    end
    users
  end

  def rm_user
    system("/usr/bin/htpasswd -D /etc/cobbler/users.digest #{@resource[:name]} 2>&1 || true")
  end

  def create_user
    File.open("/etc/cobbler/users.digest", "a+") do |file|
      file.write("#{@resource[:name]}:Cobbler:#{hashline}")
    end
  end

end
