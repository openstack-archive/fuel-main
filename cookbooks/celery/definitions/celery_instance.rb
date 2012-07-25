define :celery_instance, :virtualenv => false do
  
  node.set[:celery][:venv] = params[:virtualenv] if params[:virtualenv]
  include_recipe 'celery'

  name = params[:name]

  params[:user] ||= node.celery.user
  # validate :cwd, :kind_of => String, :required => true
  # validate :log_file, :kind_of => String
  # validate :pid_file, :kind_of => String
  # validate :log_level, :regex => /(CRITICAL|ERROR|WARNING|INFO|DEBUG)/
  # validate :events, :kind_of => [TrueClass, FalseClass]
  # validate :beat, :kind_of => [TrueClass, FalseClass]
  # validate :concurrency, :kind_of => Numeric
  # validate :extra_options, :kind_of => String

  celery_options = ''
  celery_options += " --logfile=#{params[:log_file]}" if params[:log_file]
  celery_options += " --pidfile=#{params[:pid_file]}" if params[:pid_file]
  celery_options += " -l #{params[:log_level]}" if params[:log_level]
  celery_options += " -c #{params[:concurrency]}" if params[:concurrency]
  celery_options += " -E" if params[:events]
  celery_options += " -B" if params[:beat]
  celery_options += ' ' + params[:extra_options] if params[:extra_options]

  template "/etc/init.d/#{name}" do
     source "celery-init.d.conf.erb"
     cookbook "celery"
     owner "root"
     group "root"
     mode 0755
     variables({
         :params => params,
         :celery_options => celery_options
     })
  end

  service "nailgun-jobserver" do
     supports :restart => true, :start => true, :stop => true, :reload => true
     action [:enable, :start]
  end
end
