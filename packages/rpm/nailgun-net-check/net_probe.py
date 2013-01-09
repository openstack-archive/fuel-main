#!/usr/bin/python
#
# Generate and send Ethernet packets to specified interfaces.
# Collect data from interfaces.
# Analyse dumps for packets with special cookie in UDP payload.
#
import os
import sys
import signal
import json
import socket

from subprocess import call
from optparse import OptionParser

import scapy.config as scapy
scapy.conf.logLevel = 40
scapy.conf.use_pcap = True
import scapy.all as scapy

usage = """This is a packet generator and analyser.

Run: net_probe -c <config_file>     - use config file
     net_probe -                        - read config from stdin

     net_probe -i <iface_name> -v <vlan_list> -u <UID>
                                        - generate frames

     net_probe -l <iface_name> [-d <dump_file>]
                                        - collect frames from interface

Default <dump_file> is "/var/tmp/net-probe-dump-" plus <iface_name>.
To stop listening frames send SIGINT to process.

Example run to capture frames:
net_probe -l eth0 &

Capture frames config file example is:
{"action": "listen", "interface": "eth0", 
 "dump_file": "/var/tmp/net-probe-dump-eth0"}

Simple frame generation config file example is:
{"action": "generate", "uid": "aaa-bb-cccccc", 
 "interfaces": { "eth0": "1-4094"}}

Full frame generation config file example is:
{   "action": "generate",
    "uid": "aaa-bb-cccccc", "cookie": "Some cookie",
    "src_mac": "11:22:33:44:55:66",
    "src": "10.0.0.1", "dst": "10.255.255.255",
    "sport": 4056, "dport": 4057,
    "interfaces": { 
        "eth0": "10, 15, 20, 201-210, 301-310, 1000-2000",
        "eth1": "1-4094"
    }
}
"""

def error(msg):
    sys.stderr.write(msg)

def parse_vlan_list(vlan_string):
    validate = lambda x: (x >= 0) and (x < 4095)
    chunks = vlan_string.split(",")
    vlan_list = []
    for chunk in chunks:
        delim = chunk.find("-")
        try:
            if delim > 0 :
                left = int(chunk[:delim])
                right = int(chunk[delim+1:])
                if validate(left) and validate(right):
                    vlan_list.extend(xrange(left, right+1))
                else:
                    raise ValueError
            else:
                vlan = int(chunk)
                if validate(vlan):
                    vlan_list.append(vlan)
                else:
                    raise ValueError
        except ValueError:
            error('Error: incorrect vlan: %s\n' % chunk)
            exit(1)
    return vlan_list

def get_probe_frames(iface):
    fltr = lambda r: scapy.UDP in r and str(r[scapy.UDP].payload).startswith(cookie)
    packets = scapy.sniff(iface=iface, lfilter=fltr)
    neigbors = {}
    neigbors[iface] = {}
    neigbor_dict = neigbors[iface]
    for p in packets:
        if scapy.Dot1Q in p:
            vlan = p[scapy.Dot1Q].vlan
        else:
            vlan = 0
        rmsg = str(p[scapy.UDP].payload)[len(cookie):]
        riface, uid = rmsg.split(' ', 1)
        uid = uid.strip('\x00\n')
        if vlan not in neigbor_dict:
            neigbor_dict[vlan] = {}
        if uid not in neigbor_dict[vlan]:
            neigbor_dict[vlan][uid] = [riface]
        else:
            iface_list = neigbor_dict[vlan][uid]
            if riface not in iface_list:
                iface_list.append(riface)
    return neigbors

def send_probe_frame(**props):
    for vlan in props['vlan']:
        if vlan > 0:
            iface = '%s.%d' % (props['iface'], vlan)
            iface_already_exist = not call('/sbin/ifconfig %s' % iface, shell=True)
            if not iface_already_exist:
                call(('/sbin/vconfig', 'add', props['iface'], str(vlan)))
                call(('/sbin/ifconfig', iface, 'up'))
        else:
            iface = props['iface']
        p = scapy.Ether(src=props['src_mac'], dst="ff:ff:ff:ff:ff:ff")
        p = p/scapy.IP(src=props['src'], dst=props['dst'])
        p = p/scapy.UDP(sport=props['sport'], dport=props['dport'])/props['data']
        try:
            for i in xrange(5):
                scapy.sendp(p, iface=iface)
        except socket.error, e:
            print e, iface
        if vlan > 0 and not iface_already_exist:
            call(('/sbin/ifconfig', iface, 'down'))
            call(('/sbin/vconfig', 'rem', iface))



def addpid(piddir):
    pid = os.getpid()
    if not os.path.exists(piddir):
        os.mkdir(piddir)
    pidfile = os.path.join(piddir, str(pid))
    fo = open(pidfile, 'w')
    fo.write('')
    fo.close()
    return pidfile

# -------------- main ---------------

parser = OptionParser()
parser.add_option("-d", dest="dump_file")
parser.add_option("-c", dest="config_file")
parser.add_option("-i", dest="ifname")
parser.add_option("-v", dest="vlan_list")
parser.add_option("-u", dest="uid")
parser.add_option("-l", dest="listen_iface")
opts, args = parser.parse_args()

cookie = "Nailgun:"
piddir = '/var/run/net_probe'
dumpname_prefix = "/var/tmp/net-probe-dump-"
config = {'src_mac': None,
          'src': '1.0.0.0', 'dst': '1.0.0.0',
          'sport': 31337, 'dport': 31337,
          'cookie': cookie}

if opts.config_file or '-' in args:    
    try:
        if '-' in args:
            fo = sys.stdin
        else:
            fo = open(opts.config_file, 'r')
        parsed_config = json.load(fo)
    except IOError:
        error("Error: can not read config file %s\n" % opts.config_file)
        exit(1)
    except ValueError as e:
        error("Error: can not parse config file: %s\n" % e.message)
        exit(1)
    for key in parsed_config.keys():
        config[key] = parsed_config[key]

if opts.uid:
    config['uid'] = opts.uid

if opts.ifname and opts.vlan_list:
    config['action'] = 'generate'
    config['interfaces'] = {}
    config['interfaces'][opts.ifname] = opts.vlan_list

if opts.listen_iface:
    config['action'] = 'listen'
    config['interface'] = opts.listen_iface
    if opts.dump_file:
        config['dump_file'] = opts.dump_file
    else:
        config['dump_file'] = "%s%s" % (dumpname_prefix, config['interface'])

if 'action' not in config:
    print usage
elif config['action'] == 'generate':
    if 'interfaces' not in config:
        error("Error: specify at least one 'interface-vlans' pair.")
        exit(1)
    for iface, vlan_list in config['interfaces'].items():
        props = dict(config)
        props['iface'] = iface
        props['data'] = str(''.join((config['cookie'], iface, ' ', config['uid'])))
        props['vlan'] = parse_vlan_list(vlan_list)
        send_probe_frame(**props)
elif config['action'] == 'listen':
    pidfile = addpid(piddir)
    neigbors = get_probe_frames(config['interface'])
    with open(config['dump_file'], 'w') as fo:
        fo.write(json.dumps(neigbors))
    os.unlink(pidfile)
else:
    print usage




