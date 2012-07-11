define :ssh_keygen, :length => 2048 do

  homedir = params[:homedir]
  username = params[:username]
  groupname = params[:groupname]
  keytype = params[:keytype]
  
  if not keytype =~ /^(rsa|dsa)$/
    raise Chef::Exceptions::ConfigurationError, "Wrong keytype parameter: #{keytype}"
  end

  directory homedir do
    owner username
    group groupname
    mode '755'
    recursive true
  end

  directory "#{homedir}/.ssh" do
    owner username
    group groupname
    mode '700'
  end
    
  execute "Generate ssh key for #{username}" do
    command "ssh-keygen -t #{keytype} -b #{params[:length]} -N '' -f #{homedir}/.ssh/id_#{keytype}"
    creates File.join(homedir, ".ssh", "id_#{keytype}")
    user username
    group groupname
  end
    
  file "#{homedir}/.ssh/id_#{keytype}" do
    owner username
    group groupname
    mode '600'
  end

  execute "Public ssh key for #{username}" do
    command "ssh-keygen -y -f #{homedir}/.ssh/id_#{keytype} > #{homedir}/.ssh/id_#{keytype}.pub"
    creates File.join(homedir, ".ssh", "id_#{keytype}.pub")
  end

  file "#{homedir}/.ssh/id_#{keytype}.pub" do
    owner username
    group groupname
    mode '644'
  end
end
