define :celery_instance do
  include_recipe 'celery'

  name = params[:name]

  params[:user] ||= 'vagrant'
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

  template "/etc/init/#{name}.conf" do
    source "celery-upstart.conf.erb"
    cookbook "celery"
    owner "root"
    group "root"
    mode 0644

    variables({
      :params => params,
      :celery_options => celery_options
    })

    notifies :restart, "service[#{name}]"
  end

  service name do
    provider Chef::Provider::Service::Upstart
    enabled true
    running true
    supports :restart => true, :reload => true, :status => true
    action [:enable, :start]
  end
end
