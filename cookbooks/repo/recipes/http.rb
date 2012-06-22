include_recipe "apache2"

web_app 'repo' do
  template 'apache2-site-repo.erb'
end


