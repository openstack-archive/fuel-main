
include_recipe 'django'

{ 'django-piston' => '0.2.3',
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9'
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end
end

execute 'Preseed Nailgun database' do
  command 'python manage.py loaddata nailgun/fixtures/default_env.json'
  cwd node.nailgun.root
  user node.nailgun.user
  action :nothing
end

execute 'Sync Nailgun database' do
  command 'python manage.py syncdb --noinput'
  cwd node.nailgun.root
  user node.nailgun.user
  notifies :run, resources('execute[Preseed Nailgun database]')

  not_if "test -e #{node.nailgun.root}/nailgun.sqlite"
end

redis_instance 'nailgun'

celery_instance 'nailgun-jobserver' do
  command 'python manage.py celeryd_multi'
  cwd node.nailgun.root
  events true
end

web_app 'nailgun' do
  template 'apache2-site.conf.erb'
end

