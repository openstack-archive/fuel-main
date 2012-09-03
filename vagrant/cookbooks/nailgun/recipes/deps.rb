cookbook_python_pip 'django-piston' do
  version '0.2.3-20120528'
end

{
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9',
  'django-nose' => '1.0',
  'simplejson' => '2.5.2',
  'paramiko' => '1.7.7.2',
  'ipaddr' => '2.1.10',
  'eventlet' => '0.9.17',
  'web.py' => '0.37',
  'SQLAlchemy' => '0.7.8',
  'Paste' => '1.7.5.1',
  'eventlet' => '0.9.17'
}.each do |package, version|
  python_pip package do
    version version
  end
end

