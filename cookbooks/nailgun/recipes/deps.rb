local_python_pip 'django-piston' do
  version '0.2.3-20120528'
  fromdir node[:nailgun][:eggsdir]
end

{
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9',
  'django-nose' => '1.0',
  'simplejson' => '2.5.2'
}.each do |package, version|
  local_python_pip package do
    version version
    fromdir node[:nailgun][:eggsdir]
  end
end

