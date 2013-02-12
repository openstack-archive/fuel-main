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
import time
import re
import logging
import argparse
from subprocess import call

import scapy.config as scapy
scapy.conf.logLevel = 40
scapy.conf.use_pcap = True
import scapy.all as scapy


console = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console)


class ActorFabric(object):
    @classmethod
    def getInstance(cls, config):
        if not config.get('action'):
            logger.error('Wrong config, you need define valid action')
            raise Exception('Wrong config, you need define valid action')
        if config['action'] in ('listen',):
            return Listener(config)
        elif config['action'] in ('generate',):
            return Sender(config)


class Actor(object):
    def __init__(self, config=None):
        self.config = {
            'src_mac': None,
            'src': '1.0.0.0',
            'dst': '1.0.0.0',
            'sport': 31337,
            'dport': 31337,
            'cookie': "Nailgun:",
        }
        if config:
            self.config.update(config)
        self._execute(["modprobe", "8021q"])

    def _viface_by_vid(self, vid):
        return "netprobe%d" % vid

    def _execute(self, command, expected_exit_codes=(0,)):
        logger.debug("Running command: %s" % " ".join(command))
        env = os.environ
        env["PATH"] = "/bin:/usr/bin:/sbin:/usr/sbin"
        exit_code = call(command, shell=False, env=env)
        if not exit_code in expected_exit_codes:
            logger.error("Command exited with error: %s: %s" % (" ".join(command), exit_code))


    def _viface(self, iface, vid):
        with open("/proc/net/vlan/config", "r") as f:
            for line in f:
                m = re.search(ur'(.+?)\s+\|\s+(.+?)\s+\|\s+(.+?)\s*$', line)
                if m and m.group(2) == str(vid) and m.group(3) == iface:
                    return m.group(1)
            return None


class Sender(Actor):

    def __init__(self, config=None):
        super(Sender, self).__init__(config)
        self.viface_remove_after = {}

    def ensure_vlan_iface_up(self, iface, vid):
        if not self._viface(iface, vid):
            # creating vlan interface
            self._execute([
                "ip",
                "link", "add",
                "link", iface,
                "name", self._viface_by_vid(vid),
                "type", "vlan",
                "id", str(vid)])
            # brining vlan interface up
            self._execute([
                "ip",
                "link", "set",
                "dev", self._viface_by_vid(vid),
                "up"])
            self.viface_remove_after[vid] = True

        viface = self._viface(iface, vid)
        if not viface:
            logger.error("Can not create vlan %d on "
                            "interface %s" % (vid, iface))
            raise Exception("Can not create vlan %d on "
                            "interface %s" % (vid, iface))
        return viface

    def ensure_vlan_iface_down(self, vid):
        if self.viface_remove_after.get(vid, False):
            # bringing vlan interface down
            self._execute([
                "ip",
                "link", "set",
                "dev", self._viface_by_vid(vid),
                "down"])
            # removing vlan interface
            self._execute([
                "ip",
                "link", "del",
                "dev", self._viface_by_vid(vid)])


    def parse_vlan_list(self, vlan_string):
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
                logger.error("Incorrect vlan: %s" % chunk)
                raise Exception("Incorrect vlan: %s" % chunk)
        return vlan_list

    def run(self):
        for iface, vlan_list in config['interfaces'].items():
            props = dict(self.config)
            props['iface'] = iface
            props['data'] = str(''.join((self.config['cookie'], iface, ' ', self.config['uid'])))
            props['vlan'] = self.parse_vlan_list(vlan_list)

            for vlan in props['vlan']:

                if vlan > 0:
                    viface = self.ensure_vlan_iface_up(props['iface'], vlan)
                else:
                    viface = props['iface']
                p = scapy.Ether(src=props['src_mac'], dst="ff:ff:ff:ff:ff:ff")
                p = p/scapy.IP(src=props['src'], dst=props['dst'])
                p = p/scapy.UDP(sport=props['sport'], dport=props['dport'])/props['data']
                try:
                    for i in xrange(5):
                        scapy.sendp(p, iface=viface)
                except socket.error as e:
                    logger.error("Socket error: %s, %s", e, viface)
                if vlan > 0:
                    self.ensure_vlan_iface_down(vlan)

class Listener(Actor):
    def __init__(self, config=None):
        super(Listener, self).__init__(config)
        self.pidfile = self.addpid('/var/run/net_probe')

    def addpid(self, piddir):
        pid = os.getpid()
        if not os.path.exists(piddir):
            os.mkdir(piddir)
        pidfile = os.path.join(piddir, str(pid))
        fo = open(pidfile, 'w')
        fo.write('')
        fo.close()
        return pidfile

    def run(self):
        neigbors = self.get_probe_frames(config['interface'])
        with open(config['dump_file'], 'w') as fo:
            fo.write(json.dumps(neigbors))
        os.unlink(self.pidfile)


    def get_probe_frames(self, iface):
        fltr = lambda r: scapy.UDP in r and \
            str(r[scapy.UDP].payload).startswith(self.config["cookie"])
        packets = scapy.sniff(iface=iface, lfilter=fltr)
        neigbors = {}
        neigbors[iface] = {}
        neigbor_dict = neigbors[iface]

        for p in packets:
            if scapy.Dot1Q in p:
                vlan = p[scapy.Dot1Q].vlan
            else:
                vlan = 0
            rmsg = str(p[scapy.UDP].payload)[len(self.config["cookie"]):]
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


# -------------- main ---------------

def define_parser():
    config_examples = """

Config file examples:

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

    parser = argparse.ArgumentParser(epilog=config_examples)
    parser.add_argument(
        '-c', '--config', dest='config', action='store', type=str,
        help='config file', default=None
    )
    return parser

def define_subparsers(parser):
    subparsers = parser.add_subparsers(
        dest="action", help='actions'
    )
    listen_parser = subparsers.add_parser(
        'listen', help='listen for probe packets'
    )
    listen_parser.add_argument(
        '-i', '--interface', dest='interface', action='store', type=str,
        help='interface to listen on', required=True
    )
    listen_parser.add_argument(
        '-o', '--file', dest='dump_file', action='store', type=str,
        help='file to dump captured packets', default=None
    )
    generate_parser = subparsers.add_parser(
        'generate', help='generate and send probe packets'
    )
    generate_parser.add_argument(
        '-i', '--interface', dest='interface', action='store', type=str,
        help='interface to send packets from', required=True
    )
    generate_parser.add_argument(
        '-v', '--vlans', dest='vlan_list', action='store', type=str,
        help='vlan list to send tagged packets ("100,200-300")', required=True
    )
    generate_parser.add_argument(
        '-k', '--cookie', dest='cookie', action='store', type=str,
        help='cookie string to insert into probe packets payload', default='Nailgun:'
    )
    generate_parser.add_argument(
        '-u', '--uid', dest='uid', action='store', type=str,
        help='uid to insert into probe packets payload', default='1'
    )



if __name__ == "__main__":
    parser = define_parser()
    params, other_params = parser.parse_known_args()

    config = {}
    if params.config:
        # if config file is set then we discard all other
        # command line parameters
        try:
            if params.config == '-':
                fo = sys.stdin
            else:
                fo = open(params.config, 'r')
            config = json.load(fo)
            fo.close()
        except IOError:
            logger.error("Can not read config file %s" % params.config)
            exit(1)
        except ValueError as e:
            logger.error("Can not parse config file: %s" % e.message)
            exit(1)

    else:
        define_subparsers(parser)
        params, other_params = parser.parse_known_args()

        if params.action == 'listen':
            config['action'] = 'listen'
            config['interface'] = params.interface
            if params.dump_file:
                config['dump_file'] = params.dump_file
            else:
                config['dump_file'] = "/var/tmp/net-probe-dump-%s" % config['interface']

        elif params.action == 'generate':
            config['action'] = 'generate'
            config['interfaces'] = {}
            config['interfaces'][params.interface] = params.vlan_list
            config['uid'] = params.uid
            config['cookie'] = params.cookie

    actor = ActorFabric.getInstance(config)
    actor.run()
