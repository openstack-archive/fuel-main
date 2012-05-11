# To run chef-solo from this folder use the following command:
# sudo chef-solo -l debug -c solo.rb -j solo.json

file_cache_path "/tmp/chef"
cookbook_path File.expand_path(File.join(File.dirname(__FILE__), '../cookbooks'))
