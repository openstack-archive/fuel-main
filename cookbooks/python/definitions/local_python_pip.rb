define :local_python_pip, :virtualenv => nil, :version => nil, :fromdir => nil do
  include_recipe 'python'

  package_name = "#{params[:name]}"

  if params[:virtualenv]
    pip = "#{params[:virtualenv]}/bin/pip"
  else
    pip = "pip" 
  end

  if params[:version]
    package_version = "==#{params[:version]}"
  else
    package_version = ""
  end

  if params[:fromdir]
    fromdir = params[:fromdir]
  else
    fromdir = node.python.fromdir
  end

  execute "#{pip} install #{package_name}" do
    command "#{pip} install --no-index -f file://#{fromdir} #{package_name}#{package_version}"
    only_if "which #{pip}" 
  end
end
