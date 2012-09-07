#!/usr/bin/env ruby

$LOAD_PATH.unshift(File.expand_path(File.join(File.dirname(__FILE__), "..", "lib")))

require 'naily/framework/catalog'

def usage
  puts "Usage: $0 <basedir> <nodename>"
  exit 1
end


if not ARGV[0] or not ARGV[1]
  usage
else
  basedir = ARGV[0]
  nodename = ARGV[1]
  puts Naily::Framework::Catalog.get_catalog basedir, nodename
end


