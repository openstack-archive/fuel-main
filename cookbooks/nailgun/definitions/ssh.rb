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
    
  execute "Generate ssh key for #{username}" do
    command "ssh-keygen -t #{keytype} -b #{params[:length]} -N '' -f #{homedir}/.ssh/id_#{keytype}"
    creates File.join(homedir, ".ssh", "id_#{keytype}")
    user username
    group groupname
  end
    
end
