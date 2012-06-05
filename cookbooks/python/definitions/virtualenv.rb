define :virtualenv, :site_packages => false do
  include_recipe 'python'

  if params[:path]
    venvpath = params[:path]
  else
    venvpath = params[:name]
  end

  if params[:site_packages]
    site_packages = ""
  else
    site_packages = "--no-site-packages"
  end

  execute "virtualenv #{venvpath}" do
    command "virtualenv #{site_packages} #{venvpath}"
    not_if "test -d #{venvpath}"
  end
end
