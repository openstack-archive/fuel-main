module Puppet
  newtype(:cobbler_repo) do
  @doc = "Set up a cobbler repo"

  ensurable

  newparam(:name, :namevar => true) do
    desc "The name of the repo"
  end
  newparam(:arch) do
    desc "The CPU architecture of the repo"
  end
  newparam(:breed) do
    desc "What type of repo, rsync, yum, rhn"
  end
  newparam(:comment) do
    desc "A comment for the repo"
  end
  newparam(:flags) do
    desc "Extra createrepo flags to pass"
  end
  newparam(:env) do
    desc "Environment Variables"
  end
  newparam(:keepupdated) do
    desc "Keep the repo updated"
  end
  newparam(:mirror) do
    desc "The location of the repository"
  end
  newparam(:mirrorlist) do
    desc "The location of the repository"
  end
  newparam(:mirrorlocally) do
    desc "Kernel options to append to the installed system"
  end
  newparam(:priority) do
    desc "The version of opperating system, fedora13, rhel6, virtio26"
  end
  newparam(:yumopts) do
    desc "Options to use for yum/debmirror"
  end
end
end

Puppet::Type.type(:cobbler_repo).provide(:rhcobbler_repo) do
  desc "Red Hat support for cobbler, should work on any cobbler install"

  def create
    opts = {
      :name => '--name',
      :arch => '--arch',
      :breed => '--breed',
      :comments => '--comment',
      :flags => '--createrepo-flags',
      :env => '--environment',
      :keepupdated => '--keep-updated',
      :mirror => '--mirror',
      :mirrorlist => '--mirrorlist',
      :mirrorlocally => '--mirror-locally',
      :priority => '--priority',
      :yumopts => '--yumopts',
      }
    cmd = 'cobbler repo edit '
    if `cobbler repo report --name=#{@resource[:name]}`.match(/^No/)
      cmd = 'cobbler repo add '
    end
    @resource.to_hash.each do |key, value|
      opt = opts[key]
      if opt
        if opt.match(/mirrorlist/)
          baseurl = `curl -s \"#{value}\"`
          Puppet.info "cobbler_repo: repo maps to url #{baseurl}"
          cmd << " --mirror='#{baseurl}'"
        else
          cmd << " #{opt}='#{value}'"
        end
      end
    end
    `#{cmd}`
    Puppet.info "cobbler_repo: repo created and sync started: #{@resource[:name]}"
    sync
   
  end

  def destroy
    `cobbler repo remove --name=#{@resource[:name]}`
  end
  def sync
    `cobbler reposync --only=#{@resource[:name]}`
  end 
  def exists?
    rep = `cobbler repo report --name=#{@resource[:name]}`
    if `cobbler repo report --name=#{@resource[:name]}`.match(/^No/)
      Puppet.info "cobbler_repo: repo does not exist: #{@resource[:name]}"
      return false
    end
    avail = { 
      "Name" => :name,
      "Architecture" => :arch,
      "Breed" => :breed,
      "Comment" => :comment,
      "Createrepo Flags" => :flags,
      "Environment Variables" => :env,
      "Keep Updated" => :keepupdated,
      "Mirror" => :mirror,
      "Mirrorlist" => :mirrorlist,
      "Mirror locally" => :mirrorlocally,
      "Priority" => :priority,
      "Yumopts" => :yumopts,
      }
    rep.each do |line|
      val = avail[line.split(":")[0].strip]
      unless val
        next
      end
      unless @resource[val]
        next
      end
      if val
        stat = line.split(":", 2)[1].strip
        if stat.match(/^\{/)
          stat.gsub!('{', '')
          stat.gsub!('}', '')
          stat.gsub!('\'', '')
          stat.gsub!(': ', '=')
          stat.gsub!(',', ' ')
        elsif stat.match(/^\[/)
          stat.gsub!('[', '')
          stat.gsub!(']', '')
          stat.gsub!('\'', '')
          stat.gsub!(' ', '')
          stat.gsub!(',', ' ')
        end
        unless @resource[val] == stat
          return false
        end
      end
    end
    Puppet.info "cobbler_repo: repo exists: #{@resource[:name]}"
    return true
  end
end
