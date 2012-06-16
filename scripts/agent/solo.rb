# To run chef-solo from this folder use the following command:
# sudo chef-solo -l debug -c solo.rb -j solo.json

log_location "/var/log/chef/solo.log"
file_cache_path "/tmp/chef"
cookbook_path File.expand_path(File.join(File.dirname(__FILE__), '../../cookbooks'))
log_level :debug
verbose_logging true
