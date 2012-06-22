define :distro do
  name = params[:name]
  kernel = params[:kernel]
  initrd = params[:initrd]
  arch = params[:arch]
  breed = params[:breed] #ubuntu
  osversion = params[:osversion] #precise

  execute "add_distro_#{name}" do 
    command "cobbler distro add \
--name=#{name} \
--kernel=#{kernel} \
--initrd=#{initrd} \
--arch=#{arch} \
--breed=#{breed} \
--os-version=#{osversion}"
    action :run
    only_if "test -z `cobbler distro find --name #{name}`"
  end

  execute "edit_distro_#{name}" do 
    command "cobbler distro edit \
--name=#{name} \
--kernel=#{kernel} \
--initrd=#{initrd} \
--arch=#{arch} \
--breed=#{breed} \
--os-version=#{osversion}"
    action :run
    only_if "test ! -z `cobbler distro find --name #{name}`"
  end

end
