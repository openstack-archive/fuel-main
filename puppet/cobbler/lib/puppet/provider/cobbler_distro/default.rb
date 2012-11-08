require 'puppet'
Puppet::Type.type(:cobbler_distro).provide(:default) do
  defaultfor :operatingsystem => [:centos, :redhat, :debian, :ubuntu]
  
  def exists?
    Puppet.info "cobbler_distro: checking if distro exists: #{@resource[:name]}"
    if find_distro_full
      Puppet.info "cobbler_distro: distro exists: #{@resource[:name]}"
      return true
    else
      Puppet.info "cobbler_distro: distro does not exist: #{@resource[:name]}"
      return false
    end
  end

  def create
    Puppet.info "cobbler_distro: updating distro: #{@resource[:name]}"
    update_distro
  end

  def destroy
    Puppet.info "cobbler_distro: removing distro: #{@resource[:name]}"
    remove_distro
  end

  private
  
  def ksmeta
    if @resource[:ksmeta].size > 0
      "--ksmeta=\"#{@resource[:ksmeta]}\""
    else
      ""
    end
  end

  def find_distro_full
    distro = `cobbler distro find --name=#{@resource[:name]} --kernel=#{@resource[:kernel]} --initrd=#{@resource[:initrd]} --arch=#{@resource[:arch]} --breed=#{@resource[:breed]} --os-version=#{@resource[:osversion]} #{ksmeta}`
    distro.chomp
    return distro.size != 0
  end

  def find_distro_name
    distro = `cobbler distro find --name=#{@resource[:name]}`
    distro.chomp
    return distro.size != 0
  end

  def update_distro
    subcommand = find_distro_name ? 'edit' : 'add'
    system("cobbler distro #{subcommand} --name=#{@resource[:name]} --kernel=#{@resource[:kernel]} --initrd=#{@resource[:initrd]} --arch=#{@resource[:arch]} --breed=#{@resource[:breed]} --os-version=#{@resource[:osversion]} #{ksmeta}")
  end

  def remove_distro
    system("cobbler distro remove --name=#{@resource[:name]}")
  end

end
