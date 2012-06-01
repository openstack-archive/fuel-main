default["redis2"]["install_from"] = "package"
default["redis2"]["log_dir"] =  "/var/log/redis"
default["redis2"]["conf_dir"] = "/etc/redis"
default["redis2"]["pid_dir"] = "/var/run/redis"
default["redis2"]["user"] =     "redis"
default["redis2"]["instances"]["default"]["bindaddress"] = "0.0.0.0"
default["redis2"]["instances"]["default"]["port"] = "6379"
default["redis2"]["instances"]["default"]["timeout"] = 300
default["redis2"]["instances"]["default"]["dumpdb_filename"] = "dump.rdb"
default["redis2"]["instances"]["default"]["data_dir"] = "/var/lib/redis"
default["redis2"]["instances"]["default"]["activerehashing"] = "yes" # no to disable, yes to enable
default["redis2"]["instances"]["default"]["databases"] = 16

default["redis2"]["instances"]["default"]["appendonly"] = "no"
default["redis2"]["instances"]["default"]["appendfsync"] = "everysec"
default["redis2"]["instances"]["default"]["no_appendfsync_on_rewrite"] = "no"

default["redis2"]["instances"]["default"]["vm"]["enabled"] = "no" # no to disable, yes to enable
default["redis2"]["instances"]["default"]["vm"]["swap_file"] = "/var/lib/redis/swap"
default["redis2"]["instances"]["default"]["vm"]["max_memory"] = node["memory"]["total"].to_i * 1024 * 0.7
default["redis2"]["instances"]["default"]["vm"]["page_size"] = 32 # bytes
default["redis2"]["instances"]["default"]["vm"]["pages"] = 134217728 # swap file size is pages * page_size
default["redis2"]["instances"]["default"]["vm"]["max_threads"] = 4

default["redis2"]["instances"]["default"]["maxmemory_samples"] = 3
default["redis2"]["instances"]["default"]["maxmemory_policy"] = "volatile-lru"
default["redis2"]["instances"]["default"]["bgsave"] = true
