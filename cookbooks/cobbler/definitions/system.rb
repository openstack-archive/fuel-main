define :system, :netboot => true do
  name = params[:name]
  profile = params[:profile]
  if params[:netboot] == true
    netboot = "True"
  else
    netboot = "False"
  end

  execute "add_system_#{default}" do
    command "cobbler system add \
--name=#{name} \
--profile=#{profile} \
--netboot-enabled=#{netboot}"
    action :run
    only_if "test -z `cobbler profile find --name #{name}`"
  end

  execute "edit_system_#{name}" do
    command "cobbler system edit \
--name=#{name} \
--profile=#{profile} \
--netboot-enabled=#{netboot}"
    action :run
    only_if "test ! -z `cobbler profile find --name #{name}`"
  end

end
