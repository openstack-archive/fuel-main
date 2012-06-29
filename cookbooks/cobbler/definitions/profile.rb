define :cobbler_profile, :menu => true, :kickstart => nil do
  name = params[:name]
  kopts = params[:kopts]
  distro = params[:distro]

  if params[:menu] == true
    menu = "True"
  else
    menu = "False"
  end
  
  if params[:kickstart]
    kickstart = "--kickstart=#{params[:kickstart]}"
  else
    kickstart = ""
  end


  execute "add_profile_#{name}" do
    command "cobbler profile add \
--name=#{name} \
--distro=#{distro} \
--enable-menu=#{menu} \
--kopts=\"#{kopts}\" \
#{kickstart}"
    action :run
    only_if "test -z `cobbler profile find --name #{name}`"
  end

  execute "edit_profile_#{name}" do
    command "cobbler profile edit \
--name=#{name} \
--distro=#{distro} \
--enable-menu=#{menu} \
--kopts=\"#{kopts}\" \
#{kickstart}"
    action :run
    only_if "test ! -z `cobbler profile find --name #{name}`"
  end
end
