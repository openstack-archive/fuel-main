# Installs redis from packages

pkg = value_for_platform( [:ubuntu, :debian] => {:default => "redis-server"},
                         [:centos, :redhat] => {:default => "redis"},
                         :default => "redis")
package pkg
node["redis2"]["daemon"] = "/usr/bin/redis-server"
