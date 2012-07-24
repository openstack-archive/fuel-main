# To run chef-solo from this folder use the following command:
# sudo chef-solo -l debug -c solo.rb -j solo.json
#require 'syslog_logger'

#log_location SyslogLogger.new("chef-solo")
log_location open("| logger -t chef-solo", "w")

file_cache_path "/tmp/chef"
cookbook_path File.expand_path(File.join(File.dirname(__FILE__), '../../vagrant/cookbooks'))
