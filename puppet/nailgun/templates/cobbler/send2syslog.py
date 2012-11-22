#!/usr/bin/python

import os
import sys
import signal
import string
import re
import json
import time
import logging
from logging.handlers import SysLogHandler
from optparse import OptionParser, OptionGroup


class WatchedFile:
    """ WatchedFile(filename) => Object that read lines from file if exist. """

    def __init__(self, name):
        self.name = name
        self.fo = None
        self.where = 0

    def reset(self):
        if self.fo:
            self.fo.close()
            self.fo = None
            self.where = 0

    def _checkRewrite(self):
        try:
            if os.stat(self.name)[6] < self.where:
                self.reset()
        except OSError:
            self.close()

    def readLines(self):
        """Return list of last append lines from file if exist. """

        self._checkRewrite()
        if not self.fo:
            try:
                self.fo = open(self.name, 'r')
            except IOError:
                return ()
        lines = self.fo.readlines()
        self.where = self.fo.tell()
        return lines

    def close(self):
        self.reset()

# Define data and message format according to RFC 5424.
rfc5424_format = '{version} {timestamp} {hostname} {appname} {procid}'\
                 ' {msgid} {structured_data} {msg}'
date_format = '%Y-%m-%dT%H:%M:%SZ'


class WatchedGroup:
    """ Can send data from group of specified files to specified servers. """

    def __init__(self, servers, files, name):
        self.servers = servers
        self.files = files
        self.name = name
        self._createLogger()

    def _createLogger(self):
        self.watchedfiles = []
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        # Create log formatter.
        format_dict = {'version': '1',
                       'timestamp': '%(asctime)s',
                       'hostname': config['hostname'],
                       'appname': self.files['tag'],
                       'procid': '-',
                       'msgid': '-',
                       'structured_data': '-',
                       'msg': '%(message)s'
                       }
        log_format = rfc5424_format.format(**format_dict)
        formatter = logging.Formatter(log_format, date_format)
        # Add log handler for each server.
        for server in self.servers:
            port = 'port' in server and server['port'] or 514
            syslog = SysLogHandler((server["host"], port))
            syslog.setFormatter(formatter)
            logger.addHandler(syslog)
        self.logger = logger
        # Create WatchedFile objects from list of files.
        for name in self.files['files']:
            self.watchedfiles.append(WatchedFile(name))

    def send(self):
        """ Send append data from files to servers. """

        for watchedfile in self.watchedfiles:
            for line in watchedfile.readLines():
                self.logger.info(line.strip())
                main_logger and main_logger.info(
                    'From file "%s" send: %s' % (watchedfile.name, line))


def sigint_handler(signum, frame):
    """ Send all new data when SIGINT arrived. """
    if not sending_in_progress:
        send_all()
        exit(0)
    else:
        pass


def send_all():
    """ Send any updates. """

    sending_in_progress = 1
    for group in watchlist:
        group.send()
    sending_in_progress = 0


def main_loop():
    """ Periodicaly call sendlogs() for each group in watchlist. """

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    while watchlist:
        time.sleep(0.5)
        send_all()
        # If asked to run_once, exit now
        if config['run_once']:
            break


def cmdlineParse():
    """ Parse command line config options. """

    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config_file", metavar="FILE",
                      help="Read config from FILE.")
    parser.add_option("-i", "--stdin", dest="stdin_config", default=False,
                      action="store_true", help="Read config from Stdin.")
# FIXIT Add optionGroups.
    parser.add_option("-r", "--run-once", dest="run_once", action="store_true",
                      help="Send all data and exit.")
    parser.add_option("-n", "--no-daemon", dest="no_daemon",
                      action="store_true", help="Do not daemonize.")
    parser.add_option("-d", "--debug", dest="debug",
                      action="store_true", help="Print debug messages.")

    parser.add_option("-t", "--tag", dest="tag", metavar="TAG",
                      help="Set tag of sending messages as TAG.")
    parser.add_option("-f", "--watchfile", dest="watchfiles", action="append",
                      metavar="FILE", help="Add FILE to watchlist.")
    parser.add_option("-s", "--host", dest="host", metavar="HOSTNAME",
                      help="Set destination as HOSTNAME.")
    parser.add_option("-p", "--port", dest="port", type="int", default=514,
                      metavar="PORT",
                      help="Set remote port as PORT (default: %default).")

    options, args = parser.parse_args()
    # Validate gathered options.
    if options.config_file and options.stdin_config:
        parser.error("You must not set both options --config"
                     " and --stdin at the same time.")
        exit(1)
    if ((options.config_file or options.stdin_config) and
            (options.tag or options.watchfiles or options.host)):
        main_logger.warning("If --config or --stdin is set up options"
                            " --tag, --watchfile, --host and --port"
                            " will be ignored.")
    if (not (options.config_file or options.stdin_config) and
            not (options.tag and options.watchfiles and options.host)):
        parser.error("Options --tag, --watchfile and --host"
                     "must be set up at the same time.")
        exit(1)
    return options, args


def getHostname():
    """ Generate hostname by BOOTIF kernel option or use os.uname()."""

    with open('/proc/cmdline') as fo:
        cpu_cmdline = fo.readline().strip()
    regex = re.search('(?<=BOOTIF=)([0-9a-fA-F-]*)', cpu_cmdline)
    if regex:
        mac = regex.group(0).upper()
        return ''.join(mac.split('-'))
    else:
        return os.uname()[1]


def getConfig():
    """ Generate config from command line arguments and config file. """

    # example_config = {
    #       "daemon": True,
    #       "run_once": False,
    #       "debug": False,
    #       "watchlist": [
    #           {"servers": [ {"host": "localhost", "port": 514} ],
    #           "watchfiles": [
    #               {"tag": "anaconda",
    #               "files": ["/tmp/anaconda.log",
    #                   "/mnt/sysimage/root/install.log"]
    #               }
    #               ]
    #           }
    #           ]
    #       }

    default_config = {"daemon": True,
                      "run_once": False,
                      "debug": False,
                      "hostname": getHostname(),
                      "watchlist": []
                      }
    # First use default config as running config.
    config = dict(default_config)
    # Get command line options and validate it.
    cmdline = cmdlineParse()[0]
    # Check config file source and read it.
    if cmdline.config_file or cmdline.stdin_config:
        try:
            if cmdline.stdin_config is True:
                fo = sys.stdin
            else:
                fo = open(cmdline.config_file, 'r')
            parsed_config = json.load(fo)
            if cmdline.debug:
                print parsed_config
        except IOError:  # Raised if IO operations failed.
            main_logger.error("Can not read config file %s\n" %
                              cmdline.config_file)
            exit(1)
        except ValueError as e:  # Raised if json parsing failed.
            main_logger.error("Can not parse config file. %s\n" %
                              e.message)
            exit(1)
        #  Validate config from config file.
        configValidate(parsed_config)
        # Copy gathered config from config file to running config structure.
        for key, value in parsed_config.items():
            config[key] = value
    else:
        # If no config file specified use watchlist setting from command line.
        watchlist = {"servers": [{"host": cmdline.host,
                                  "port": cmdline.port}],
                     "watchfiles": [{"tag": cmdline.tag,
                                     "files": cmdline.watchfiles}]}
        config['watchlist'].append(watchlist)

    # Apply behavioural command line options to running config.
    if cmdline.no_daemon:
        config["daemon"] = False
    if cmdline.run_once:
        config["run_once"] = True
    if cmdline.debug:
        config["debug"] = True
    return config


def type2str(value):
    """ Return text description of type of value. """

    definitions = ((basestring, "string"), (int, "int"), (dict, "dict"),
                   (list, "list"), (bool, "bool"))
    for i in definitions:
        if (isinstance(value, type) and value or type(value)) is i[0]:
            return i[1]
    else:
        return str(value)


def checkType(value, value_type, value_name='', msg=None):
    """ Check correctness of type of value and exit if not. """

    if not isinstance(value, value_type):
        message = msg or "Value %r in config have type %r but"\
            " %r is expected." %\
            (value_name, type2str(value), type2str(value_type))
        main_logger.error(message)
        exit(1)


def configValidate(config):
    """ Validate types and names of data items in config. """

    checkType(config, dict, msg='Config must be a dict.')
    for key in ("daemon", "run_once", "debug"):
        if key in config:
            checkType(config[key], bool, key)
    key = "hostname"
    if key in config:
        checkType(config[key], basestring, key)

    key = "watchlist"
    if key in config:
        checkType(config[key], list, key)
    else:
        main_logger.error("There must be key %r in config." % key)
        exit(1)

    for item in config["watchlist"]:
        checkType(item, dict, "watchlist[n]")
        key, name = "servers", "watchlist[n]  => servers"
        if key in item:
            checkType(item[key], list, name)
        else:
            main_logger.error("There must be key %r in %s in config." %
                              (key, '"watchlist[n]" item'))
            exit(1)
        key, name = "watchfiles", "watchlist[n] => watchfiles"
        if key in item:
            checkType(item[key], list, name)
        else:
            main_logger.error("There must be key %r in %s in config." %
                              (key, '"watchlist[n]" item'))
            exit(1)

        for item2 in item["servers"]:
            checkType(item2, dict, "watchlist[n]  => servers[n]")
            key, name = "host", "watchlist[n]  => servers[n] => host"
            if key in item2:
                checkType(item2[key], basestring, name)
            else:
                main_logger.error("There must be key %r in %s in config." %
                                  (key, '"watchlist[n] => servers[n]" item'))
                exit(1)
            key, name = "port", "watchlist[n]  => servers[n] => port"
            if key in item2:
                checkType(item2[key], int, name)

        for item2 in item["watchfiles"]:
            checkType(item2, dict, "watchlist[n]  => watchfiles[n]")
            key, name = "tag", "watchlist[n]  => watchfiles[n] => tag"
            if key in item2:
                checkType(item2[key], basestring, name)
            else:
                main_logger.error("There must be key %r in %s in config." %
                                  (key,
                                   '"watchlist[n] => watchfiles[n]" item'))
                exit(1)
            key, name = "files", "watchlist[n]  => watchfiles[n] => files"
            if key in item2:
                checkType(item2[key], list, name)
            else:
                main_logger.error("There must be key %r in %s in config." %
                                  (key,
                                   '"watchlist[n] => watchfiles[n]" item'))
                exit(1)
            for item3 in item2["files"]:
                checkType(item3, basestring,
                          "watchlist[n]  => watchfiles[n] => files[n]")


# Define global semaphore
sending_in_progress = 0
# Create a main logger.
logging.basicConfig(format='%(levelname)s: %(message)s')
main_logger = logging.getLogger()
main_logger.setLevel(logging.INFO)

config = getConfig()
# Create list of WatchedGroup objects with different log names.
watchlist = []
i = 0
for item in config["watchlist"]:
    for files in item['watchfiles']:
        watchlist.append(WatchedGroup(item['servers'], files, str(i)))
        i = i + 1

# Fork and loop
if config["daemon"]:
    if not os.fork():
        # Redirect the standard I/O file descriptors to the specified file.
        main_logger = None
        DEVNULL = getattr(os, "devnull", "/dev/null")
        os.open(DEVNULL, os.O_RDWR)  # standard input (0)
        os.dup2(0, 1)  # Duplicate standard input to standard output (1)
        os.dup2(0, 2)  # Duplicate standard input to standard error (2)

        main_loop()
        sys.exit(1)
    sys.exit(0)
else:
    if not config['debug']:
        main_logger = None
    main_loop()
