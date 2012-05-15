
{ 'django-piston' => '0.2.3',
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9',
  'django-nose' => '1.0',
  'simplejson' => '2.5.2'
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end
end

