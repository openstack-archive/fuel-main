#!/usr/bin/python
#
# Generate and send Ethernet packets to specified interfaces.
# Analyse pcap dumps for packets with special cookie in UDP payload.
#
# Run: net_probe -c <config_filename>    - use config file.
#      net_porbe -                       - read config from stdin.
#      net_probe -i <iface_name> -v <vlan_list> -u <UID>
#                                        - generate frames.
#      net_probe -f <pcap_filename>      - analyse dump.
import os
import sys
import json

from optparse import OptionParser
from scapy.all import *

def parse_vlan_list(vlan_string):
    chunks = vlan_string.split(",")
    vlan_list = []
    for chunk in chunks:
        delim = chunk.find("-")
        if delim > 0 :
            left = int(chunk[:delim])
            right = int(chunk[delim+1:])
            vlan_list.append((left, right))
        else:
            vlan_list.append(int(chunk))
    return vlan_list

def send_probe_frame(iface, vlan, data, src_mac="00:00:00:00:00:00",
                     src="127.0.0.1", dst="127.0.0.1", sport=31337, dport=31337):
    p = Ether(src=src_mac)/Dot1Q(vlan=vlan)/IP(src=src, dst=dst)
    p = p/UDP(sport=sport, dport=dport)/data
    sendp(p, iface=iface)

def analyse_dump(filename):
    dump = rdpcap(filename)
    dump = dump.filter(lambda r: UDP in r and str(r[UDP].payload).startswith(cookie))
    neigbor_dict = {}
    for packet in dump:
#        rmac = packet[Ether].src
        rvlan = packet[Dot1Q].vlan
        rmsg = str(packet[UDP].payload)[len(cookie):]
        riface, ruid = rmsg.split(' ')
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
parser.add_option("-f", dest="dump_file")
parser.add_option("-c", dest="config_file")
parser.add_option("-i", dest="ifname")
parser.add_option("-v", dest="vlan_list")
parser.add_option("-u", dest="uid")
opts, args = parser.parse_args()

cookie = "Nailgun: "

if opts.config_file or '-' in args:    
    try:
        if '-' in args:
            fo = sys.stdin
        else:
            fo = open(opts.config_file, 'r')
        opts = json.load(fo)
    except IOError:
        print "Error: can not read config file %s\n" % opts.config_file
        exit(1)
    except ValueError as e:
        print "Error: can not parse config file: %s\n" % e.strerror
        exit(1)

    if opts.has_key('uid'):
        uid = opts['uid']
    else:
        print "Error: specify uid in config.\n"
    if opts.has_key('cookie'):
        cookie = opts['cookie']

    prop_list = ('src_mac', 'src', 'dst', 'sport', 'dport')
    props = {}
    for i in prop_list:
        if opts.has_key(i):
            props[i] = opts[i]

    if opts.has_key('interfaces'):
        for iface, vlan_list in opts['interfaces'].items():
            props['iface'] = iface
            props['data'] = str(''.join((cookie, iface, ' ', uid)))
            try:
                props['vlan'] = parse_vlan_list(vlan_list)
            except ValueError, IndexError:
                print "Warning: can not parse vlan list for %s\n" % iface
            except:
                print "Warning: can not send packets to \
interface %s: %s\n" % (iface, sys.exc_info()[0])
            send_probe_frame(**props)
    else:
        print "Error: specify 'interfaces' section in config file."
        exit(1)

elif opts.dump_file:
    if not os.access(opts.dump_file, os.R_OK):
        print "Error: can not read dump file %s\n" % opts.dump_file
        exit(1)
    try:
        neigbors = analyse_dump(opts.dump_file)
    except:
        print "Error: can not analyse dump: %s\n" % opts.dump_file
        exit(1)
    print json.dumps(neigbors)
    exit(0)
elif opts.ifname and opts.vlan_list and opts.uid:
    vlist = parse_vlan_list(opts.vlan_list)
    iface = opts.ifname
    uid = opts.uid
    send_probe_frame(iface, vlist, ''.join((cookie, iface, ' ', uid)))
else:
    print """This is packet generator and analyser.
Run: net_probe -c <config_filename>     - use config file.
     net_probe -                        - read config from stdin.
     net_probe -i <iface_name> -v <vlan_list> -u <UID>
                                        - generate frames.
     net_probe -f <pcap_filename>       - analyse dump.

Simple config file example is:
{"uid": "aaa-bb-cccccc", "interfaces": { "eth0": "1-4094"}}

Full config file example is:
{   "uid": "aaa-bb-cccccc", "cookie": "Some cookie",
    "src_mac": "11:22:33:44:55:66",
    "src": "10.0.0.1", "dst": "10.255.255.255",
    "sport": 4056, "dport": 4057,
    "interfaces": { 
        "eth0": "10, 15, 20, 201-210, 301-310, 1000-2000",
        "eth1": "1-4094"
    }
}
"""





