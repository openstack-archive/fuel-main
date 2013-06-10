#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

import os
import sys
import threading
import argparse
import time
import tftpy

tftpy.setLogLevel(logging.WARNING)

class TClient(threading.Thread):
    def __init__(self, hostname, port, remote_filename, local_filename=None):
        logger.debug("Initializing TClient instance: "
                     "hostname: '%s' port: %s remote file: '%s' local file: '%s'",
                     hostname, port, remote_filename, local_filename)
        super(TClient, self).__init__()
        self.hostname = hostname
        self.port = port
        self.remote_filename = remote_filename
        self.local_filename = local_filename
        self.daemon = True
        if not self.local_filename:
            self.local_filename = os.devnull

    def run(self):
        self.client = tftpy.TftpClient(self.hostname, self.port)
        self.client.download(self.remote_filename, self.local_filename)

    def stat(self):
        s = self.client.context.metrics
        return (s.bytes, s.duration, s.kbps)


def term_handler(signum, sigframe):
    sys.exit()


def parse_arguments():
    description = """
This script is for testing TFTP servers.
Example: ./tftp_client.py -a localhost -p 69 -f tftpfile -n 2
    """

    parser = argparse.ArgumentParser(epilog=description)
    parser.add_argument(
        '-a', '--host', dest='host', action='store', type=str,
        help='hostname where TFTP server listens', required=True
    )
    parser.add_argument(
        '-p', '--port', dest='port', action='store', type=int,
        help='port where TFTP server listens', required=True
    )
    parser.add_argument(
        '-f', '--file', dest='file', action='store', type=str,
        help='filename on TFTP server', required=True
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store', type=str,
        help='output path prefix for output files, '
        'will be appended with thread number. '
        '/dev/null will be used if not set', default=None
    )
    parser.add_argument(
        '-n', '--num_threads', dest='num_threads', action='store', type=int,
        help='number TFTP threads', required=True
    )
    params, other_params = parser.parse_known_args()
    return [params, other_params]

if __name__ == "__main__":

    params, other_params = parse_arguments()
    clients = []
    for i in xrange(params.num_threads):
        logger.debug("Thread: %s", i)
        o = params.output
        if params.output:
            o = "%s%05d" % (params.output, i)
        client = TClient(params.host, params.port, params.file, o)
        clients.append(client)
        logger.debug("===")
        clients[-1].start()

    try:
        while True:
            if not any(map(lambda c: c.isAlive(), clients)):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logger.debug("Interruption signal catched")
        sys.exit(0)
    except SystemExit:
        logger.debug("TERM signal catched")

    for i, c in enumerate(clients):
        logger.debug("Statistics tftp client thread: %s", i)
        logger.info("Bytes: %s, Duration: %s, Speed: %s kbps" % c.stat())

