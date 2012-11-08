require 'puppet'
Puppet::Type.type(:cobbler_profile).provide(:default) do
  defaultfor :operatingsystem => [:centos, :redhat, :debian, :ubuntu]
  
  def exists?
    Puppet.info "cobbler_profile: checking if profile exists: #{@resource[:name]}"
    if find_profile_full
      Puppet.info "cobbler_profile: profile exists: #{@resource[:name]}"
      return true
    else
      Puppet.info "cobbler_profile: profile does not exist: #{@resource[:name]}"
      return false
    end
  end

  def create
    Puppet.info "cobbler_profile: updating profile: #{@resource[:name]}"
    update_profile
  end

  def destroy
    Puppet.info "cobbler_profile: removing profile: #{@resource[:name]}"
    remove_profile
  end

  private

  def enable_menu
    if @resource[:menu] == :true
      "True" 
    else
      "False"  
    end
  end

  def kickstart
    if @resource[:kickstart].size > 0
      "--kickstart=#{@resource[:kickstart]}"
    else
      ""
    end
  end

  def ksmeta
    if @resource[:ksmeta].size > 0
      "--ksmeta=\"#{@resource[:ksmeta]}\""
    else
      ""
    end
  end

  def find_profile_full
    profile = `cobbler profile find --name=#{@resource[:name]} --distro=#{@resource[:distro]} --enable-menu=#{enable_menu} --kopts=\"#{@resource[:kopts]}\" #{kickstart} #{ksmeta}`
    profile.chomp
    return profile.size != 0
  end

  def find_profile_name
    profile = `cobbler profile find --name=#{@resource[:name]}`
    profile.chomp
    return profile.size != 0
  end

  def update_profile
    subcommand = find_profile_name ? 'edit' : 'add'
    system("cobbler profile #{subcommand} --name=#{@resource[:name]} --distro=#{@resource[:distro]} --enable-menu=#{enable_menu} --kopts=\"#{@resource[:kopts]}\" #{kickstart} #{ksmeta}")
  end

  def remove_profile
    system("cobbler profile remove --name=#{@resource[:name]}")
  end

end
