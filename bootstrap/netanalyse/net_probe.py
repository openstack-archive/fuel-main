#!/usr/bin/python
#
# Generate and send Ethernet packets to specified interfaces.
# Collect data from interfaces.
# Analyse dumps for packets with special cookie in UDP payload.
#
import os
import sys
import json

from optparse import OptionParser
from scapy.config import *
conf.logLevel = 40
from scapy.all import *

def error(msg):
    sys.stderr().write(msg)

def parse_vlan_list(vlan_string):
    validate = lambda x: (x > 0) and (x < 4095)
    chunks = vlan_string.split(",")
    vlan_list = []
    for chunk in chunks:
        delim = chunk.find("-")
        try:
            if delim > 0 :
                left = int(chunk[:delim])
                right = int(chunk[delim+1:])
                if validate(left) and validate(right):
                    vlan_list.append((left, right))
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

def print_packet(packet):
    rvlan = packet[Dot1Q].vlan
    rmsg = str(packet[UDP].payload)[len(cookie):]
    return "%d %s" % (rvlan, rmsg)

def listen_probe_frames(iface):
    fltr = lambda r: UDP in r and str(r[UDP].payload).startswith(cookie)
    sniff(iface=iface, lfilter=fltr, prn=print_packet)

def send_probe_frame(iface, vlan, data, src_mac="00:00:00:00:00:00",
                     src="0.0.0.0", dst="0.0.0.0", sport=31337, dport=31337):
    p = Ether(src=src_mac)/Dot1Q(vlan=vlan)/IP(src=src, dst=dst)
    p = p/UDP(sport=sport, dport=dport)/data
    sendp(p, iface=iface)

def analyse_dump(file_list):
    neigbors = {}
    for iface, name in file_list:
        fo = open(name, 'r')
        neigbors[iface] = {}
        neigbor_dict = neigbors[iface]
        for line in fo.readline():
            vlan, riface, uid = line.split(' ', 2)
            if not neigbor_dict.has_key(vlan):
                neigbor_dict[vlan] = {}
            if not neigbor_dict[vlan].has_key(uid):
                neigbor_dict[vlan][uid] = [riface]
            else:
                iface_list = neigbor_dict[vlan][uid]
                if riface not in iface_list:
                    iface_list.append(riface)
        fo.close()
    return neigbors

def analyse_pcap_dump(filename):
    dump = rdpcap(filename)
    dump = dump.filter(lambda r: UDP in r and str(r[UDP].payload).startswith(cookie))
    neigbor_dict = {}
    for packet in dump:
        if Dot1Q in packet:
            rvlan = packet[Dot1Q].vlan
        else:
            rvlan = 0
        rmsg = str(packet[UDP].payload)[len(cookie):]
        riface, ruid = rmsg.split(' ', 1)
        if not neigbor_dict.has_key(rvlan):
            neigbor_dict[rvlan] = {}
        if not neigbor_dict[rvlan].has_key(ruid):
            neigbor_dict[rvlan][ruid] = (riface,)
        else:
            mac_list = neigbor_dict[rvlan][ruid]
            if rmac not in mac_list:
                neigbor_dict[rvlan][ruid] = mac_list + (rmac,)
    return neigbor_dict


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
action = ""
piddir = '/var/run'

if opts.config_file or '-' in args:    
    try:
        if '-' in args:
            fo = sys.stdin
        else:
            fo = open(opts.config_file, 'r')
        conf = json.load(fo)
    except IOError:
        error("Error: can not read config file %s\n" % conf.config_file)
        exit(1)
    except ValueError as e:
        error("Error: can not parse config file: %s\n" % e.message)
        exit(1)

    if conf.has_key('uid'):
        uid = conf['uid']
    if conf.has_key('cookie'):
        cookie = conf['cookie']
    if conf.has_key('action'):
        action = conf['action']

    prop_list = ('src_mac', 'src', 'dst', 'sport', 'dport')
    props = {'src_mac': '00:00:00:00:00:00',
             'src': '0.0.0.0', 'dst': '0.0.0.0',
             'sport': 31337, 'dport': 31337}
    for i in prop_list:
        if conf.has_key(i):
            props[i] = conf[i]
    if conf.has_key('interfaces'):
        interfaces = conf['interfaces']
    else:
        error("Error: specify 'interfaces' section in config file.")
        exit(1)

if opts.uid:
    uid = opts.uid
if not uid:
    error("Error: need to specify uid.\n")
    exit(1)

if opts.ifname and opts.vlan_list:
    action = 'generate'
    vlist = parse_vlan_list(opts.vlan_list)
    interfaces[opts.ifname] = vlist
    interfaces = {}

if opts.dump_file and opts.ifname:
    action = 'analyse'
    interfaces = {}
    interfaces[opts.ifname] = opts.dump_file

if opts.listen_iface:
    action = 'listen'
    listen = opts.listen_iface

if action == 'generate':
    for iface, vlan_list in interfaces.items():
        props['iface'] = iface
        props['data'] = str(''.join((cookie, iface, ' ', uid)))
        props['vlan'] = parse_vlan_list(vlan_list)
        send_probe_frame(**props)
elif action == 'analyse':
    neigbors = analyse_dump(interfaces)
    print json.dumps({'uid':uid, 'neigbors':neigbors})
elif action = 'listen':
    pid = os.getpid()
    filename = 'net_probe.pid'
    pidfile = '/'.join((piddir, filename))
    fo = open(pidfile, 'a')
    fo.write('%d\n' % pid)
    fo.close()
    listen_probe_frames(listen)
else:
    print """This is a packet generator and analyser.
Run: net_probe -c <config_filename>     - use config file.
     net_probe -                        - read config from stdin.
     net_probe -i <iface_name> -v <vlan_list> -u <UID>
                                        - generate frames.
     net_probe -l <iface_name>          - collect frames from interface.
     net_probe -d <filename> -i <iface_name> -u <UID>
                                        - analyse dump.

Simple analyse dumps config file example is:
{"action": "generate", uid": "aaa-bb-cccccc", 
 "interfaces": { "eth0": "/var/tmp/dump-eth0"}}

Simple frame generation config file example is:
{"action": "generate", uid": "aaa-bb-cccccc", 
 "interfaces": { "eth0": "1-4094"}}

Full frame generation config file example is:
{   "uid": "aaa-bb-cccccc", "cookie": "Some cookie",
    "action": "generate",
    "src_mac": "11:22:33:44:55:66",
    "src": "10.0.0.1", "dst": "10.255.255.255",
    "sport": 4056, "dport": 4057,
    "interfaces": { 
        "eth0": "10, 15, 20, 201-210, 301-310, 1000-2000",
        "eth1": "1-4094"
    }
}
"""





