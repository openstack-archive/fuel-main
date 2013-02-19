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
import functools
import threading
from subprocess import call


import scapy.config as scapy
scapy.conf.logLevel = 40
scapy.conf.use_pcap = True
import scapy.all as scapy

class ActorFabric(object):
    @classmethod
    def getInstance(cls, config):
        if not config.get('action'):
            self.logger.error('Wrong config, you need define valid action')
            raise Exception('Wrong config, you need define valid action')
        if config['action'] in ('listen',):
            return Listener(config)
        elif config['action'] in ('generate',):
            return Sender(config)


class ActorException(Exception):
    def __init__(self, logger, message='', level='error'):
        getattr(logger, level, logger.error)(message)
        super(ActorException, self).__init__(message)


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

        self.logger.debug("Running with config: %s", json.dumps(self.config))
        self._execute(["modprobe", "8021q"])
        self.viface_remove_after = {}

    def _define_logger(self, filename, level=logging.DEBUG):
        f = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        l = logging.getLogger()
        h = logging.FileHandler(filename)
        h.setFormatter(f)
        l.addHandler(h)
        l.setLevel(level)
        return l

    def _viface_by_iface_vid(self, iface, vid):
        return "%s.%d" % (iface, vid)

    def _execute(self, command, expected_exit_codes=(0,)):
        self.logger.debug("Running command: %s" % " ".join(command))
        env = os.environ
        env["PATH"] = "/bin:/usr/bin:/sbin:/usr/sbin"
        exit_code = call(command, shell=False, env=env)
        if not exit_code in expected_exit_codes:
            raise ActorException(
                self.logger,
                "Command exited with error: %s: %s" % (" ".join(command), exit_code)
            )

    def _viface(self, iface, vid):
        with open("/proc/net/vlan/config", "r") as f:
            for line in f:
                m = re.search(ur'(.+?)\s+\|\s+(.+?)\s+\|\s+(.+?)\s*$', line)
                if m and m.group(2) == str(vid) and m.group(3) == iface:
                    return m.group(1)

    def _parse_vlan_list(self, vlan_string):
        self.logger.debug("Parsing vlan list: %s", vlan_string)
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
                raise ActorException(self.logger, "Incorrect vlan: %s" % chunk)
        self.logger.debug("Parsed vlans: %s", str(vlan_list))
        return vlan_list

    def _ensure_vlan_iface_up(self, iface, vid):
        self.logger.debug("Checking if vlan %s "
            "on interface %s already exists", str(vid), iface)
        if not self._viface(iface, vid):
            self.logger.debug("Creating vlan %s on interface %s", str(vid), iface)
            # creating vlan interface
            self._execute([
                "ip",
                "link", "add",
                "link", iface,
                "name", self._viface_by_iface_vid(iface, vid),
                "type", "vlan",
                "id", str(vid)])
            # brining vlan interface up
            self._execute([
                "ip",
                "link", "set",
                "dev", self._viface_by_iface_vid(iface, vid),
                "up"])
            self.viface_remove_after[self._viface_by_iface_vid(iface, vid)] = True

        viface = self._viface(iface, vid)
        if not viface:
            raise ActorException(
                self.logger,
                "Can not create vlan %d on interface %s" % (vid, iface)
            )
        return viface

    def _ensure_vlan_iface_down(self, iface, vid):
        if self.viface_remove_after.get(
                self._viface_by_iface_vid(iface, vid), False):
            self.logger.debug("Removing vlan interface %s",
                self._viface_by_iface_vid(iface, vid)
            )
            # bringing vlan interface down
            self._execute([
                "ip",
                "link", "set",
                "dev", self._viface_by_iface_vid(iface, vid),
                "down"])
            # removing vlan interface
            self._execute([
                "ip",
                "link", "del",
                "dev", self._viface_by_iface_vid(iface, vid)])

    def _iface_vlan_iterator(self):
        for iface, vlan_list in self.config['interfaces'].iteritems():
            for vlan in self._parse_vlan_list(vlan_list):
                yield (iface, vlan)


class Sender(Actor):

    def __init__(self, config=None):
        self.logger = self._define_logger('/root/netprobe_sender.log')
        super(Sender, self).__init__(config)
        self.logger.info("=== Starting Sender ===")

    def run(self):
        for iface, vlan in self._iface_vlan_iterator():
            data = str(''.join((self.config['cookie'], iface, ' ', self.config['uid'])))
            self.logger.debug("Sending packets: iface=%s vlan=%s", iface, str(vlan))

            if vlan > 0:
                self.logger.debug("Ensure up: %s, %s", iface, str(vlan))
                viface = self._ensure_vlan_iface_up(iface, vlan)
            else:
                viface = iface

            p = scapy.Ether(src=self.config['src_mac'], dst="ff:ff:ff:ff:ff:ff")
            p = p/scapy.IP(src=self.config['src'], dst=self.config['dst'])
            p = p/scapy.UDP(sport=self.config['sport'], dport=self.config['dport'])/data

            try:
                for i in xrange(5):
                    self.logger.debug("Sending packet: iface=%s data=%s", viface, data)
                    scapy.sendp(p, iface=viface)
            except socket.error as e:
                self.logger.error("Socket error: %s, %s", e, viface)

            if vlan > 0:
                self.logger.debug("Ensure down: %s, %s", iface, str(vlan))
                self._ensure_vlan_iface_down(iface, vlan)


class Listener(Actor):
    def __init__(self, config=None):
        self.logger = self._define_logger('/root/netprobe_listener.log')
        super(Listener, self).__init__(config)
        self.logger.info("=== Starting Listener ===")
        self.pidfile = self.addpid('/var/run/net_probe')

        self.neighbours = {}

    def addpid(self, piddir):
        pid = os.getpid()
        if not os.path.exists(piddir):
            os.mkdir(piddir)
        pidfile = os.path.join(piddir, str(pid))
        with open(pidfile, 'w') as fo:
            fo.write('')
        return pidfile

    def run(self):
        sniffers = {}

        for iface, vlan in self._iface_vlan_iterator():
            if vlan > 0:
                self.logger.debug("Ensure up: %s, %s", iface, str(vlan))
                viface = self._ensure_vlan_iface_up(iface, vlan)
            if not iface in sniffers:
                t = threading.Thread(
                    target=self.get_probe_frames,
                    args=(iface,)
                )
                t.daemon = True
                t.start()
                sniffers[iface] = t

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.config['ready_address'], self.config['ready_port']))
        except socket.error as e:
            self.logger.error("Socket error: %s", e)
        else:
            msg = "READY"
            total_sent = 0
            while total_sent < len(msg):
                sent = s.send(msg[total_sent:])
                if sent == 0:
                    raise ActorException(
                        self.logger,
                        "Socket broken. Cannot send %s status." % msg
                    )
                total_sent += sent
        finally:
            s.close()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.debug("Interruption signal catched")
        except SystemExit:
            self.logger.debug("TERM signal catched")

        for iface, vlan in self._iface_vlan_iterator():
            if vlan > 0:
                self.logger.debug("Ensure down: %s, %s", iface, str(vlan))
                self._ensure_vlan_iface_down(iface, vlan)

        with open(self.config['dump_file'], 'w') as fo:
            fo.write(json.dumps(self.neighbours))
        os.unlink(self.pidfile)

    def fprn(self, p, iface):

        if scapy.Dot1Q in p:
            vlan = p[scapy.Dot1Q].vlan
        else:
            vlan = 0

        self.logger.debug("Catched packet: vlan=%s "
                "payload=%s", str(vlan), p[scapy.UDP].payload)

        rmsg = str(p[scapy.UDP].payload)[len(self.config["cookie"]):]
        riface, uid = rmsg.split(' ', 1)
        uid = uid.strip('\x00\n')

        self.neighbours[iface].setdefault(vlan, {})

        if riface not in self.neighbours[iface][vlan].setdefault(uid, []):
            self.neighbours[iface][vlan][uid].append(riface)

    def get_probe_frames(self, iface):
        if not iface in self.neighbours:
            self.neighbours[iface] = {}

        def fltr(p):
            try:
                return scapy.UDP in p and \
                    str(p[scapy.UDP].payload).startswith(self.config["cookie"])
            except Exception as e:
                self.logger.debug("Error while filtering packet: %s", str(e))
                return False

        pprn = functools.partial(self.fprn, iface=iface)
        packets = scapy.sniff(iface=iface, lfilter=fltr, prn=pprn)


# -------------- main ---------------

def define_parser():
    config_examples = """

Config file examples:

Capture frames config file example is:
{"action": "listen", "interfaces": {"eth0": "1-4094"},
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
        '-v', '--vlans', dest='vlan_list', action='store', type=str,
        help='vlan list to send tagged packets ("100,200-300")', required=True
    )
    listen_parser.add_argument(
        '-k', '--cookie', dest='cookie', action='store', type=str,
        help='cookie string to insert into probe packets payload', default='Nailgun:'
    )
    listen_parser.add_argument(
        '-o', '--file', dest='dump_file', action='store', type=str,
        help='file to dump captured packets', default=None
    )
    listen_parser.add_argument(
        '-a', '--address', dest='ready_address', action='store', type=str,
        help='address to report listener ready state', default='localhost'
    )
    listen_parser.add_argument(
        '-p', '--port', dest='ready_port', action='store', type=int,
        help='port to report listener ready state', default=31338
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

def term_handler(signum, sigframe):
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, term_handler)

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
            print "Can not read config file %s" % params.config
            exit(1)
        except ValueError as e:
            print "Can not parse config file: %s" % str(e)
            exit(1)

    else:
        define_subparsers(parser)
        params, other_params = parser.parse_known_args()

        if params.action == 'listen':
            config['action'] = 'listen'
            config['interfaces'] = {}
            config['interfaces'][params.interface] = params.vlan_list
            config['cookie'] = params.cookie
            config['ready_address'] = params.ready_address
            config['ready_port'] = params.ready_port
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
