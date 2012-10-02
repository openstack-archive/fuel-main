#!/usr/bin/ruby
#
require 'mcollective'
include MCollective::RPC

nf = rpcclient("nailyfact")

printrpc nf.put(:key => "role", :value => "test_compute")
printrpc nf.put(:key => "meta", :value => "some_meta_value")

printrpcstats

puppet = rpcclient("puppetd")
puppet.runonce
printrpc puppet.status
sleep 5
printrpc puppet.status
