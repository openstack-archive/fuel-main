#!/usr/bin/env ruby

### network-restart.rb : thorough redhat network restarter
###
### This attempts to remove what's left behind by `service network stop`,
### which happens when you remove device configuration files.
###
### Camille Meulien     <cmeulien@heliostech.fr>
### Elie Bleton         <ebleton@heliostech.fr>

#   Copyright 2011 Helios Technologies SARL
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

fail "usage: #{__FILE__} --sure" if ARGV.first != "--sure"

def ifaces
  `ifconfig | grep -E '^[^ ]' | cut -d' ' -f1`.split.map { |d| d.chomp }
end

@cmds, @bridges, @bridge = [], {}, nil

# Try to stop properly :)
@cmds << "service network stop"

# Remove interfaces
ifaces.each { |iface| @cmds <<  "ip link set #{iface} down" }

# Remove bridges
`brctl show`.split("\n")[1..-1].each do |line|
  if line =~ /^([^\t]+)\t+[^\t]+\t+[^\t]+\t+([^\t]+)$/
    @bridge, iface = $1, $2
    @bridges[@bridge] = [ iface ]
  elsif line =~ /^ +([^ ]+)$/
    @bridges[@bridge] << (iface = $1)
  else
    STDERR.puts "brctl parse error:" + line
  end
end

@bridges.each_pair do |bridge, iflist|
  iflist.each { |iface| @cmds << "brctl delif #{bridge} #{iface}" }
  @cmds << "brctl delbr #{bridge}"
end

# Remove DHCP client
daemons = ["dhclient", "udhcpcd", "dhcpcd"]
daemons.each { |p| @cmds << "killall -KILL #{p}" if `ps x`.include?(p) }

# Delete all links
ifaces.each { |iface| @cmds <<  "ip link delete #{iface}" }

# Remove bonding module
@cmds << "rmmod bonding" if `lsmod | egrep '^bonding'`.chomp.empty?

# Guess what ??
@cmds << "service network restart"

# Exec
@cmds.each do |cmd|
  puts cmd
  system cmd
end
