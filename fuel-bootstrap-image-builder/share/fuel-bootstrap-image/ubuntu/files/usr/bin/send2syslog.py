#!/usr/bin/env python

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import logging
from logging.handlers import SysLogHandler
from optparse import OptionParser
import os
import re
import signal
import sys
import time


# Add syslog levels to logging module.
logging.NOTICE = 25
logging.ALERT = 60
logging.EMERG = 70
logging.addLevelName(logging.NOTICE, 'NOTICE')
logging.addLevelName(logging.ALERT, 'ALERT')
logging.addLevelName(logging.EMERG, 'EMERG')
SysLogHandler.priority_map['NOTICE'] = 'notice'
SysLogHandler.priority_map['ALERT'] = 'alert'
SysLogHandler.priority_map['EMERG'] = 'emerg'
# Define data and message format according to RFC 5424.
rfc5424_format = '{version} {timestamp} {hostname} {appname} {procid}'\
                 ' {msgid} {structured_data} {msg}'
date_format = '%Y-%m-%dT%H:%M:%SZ'
# Define global semaphore.
sending_in_progress = 0
# Define file types.
msg_levels = {'ruby': {'regex': '(?P<level>[DIWEF]), \[[0-9-]{10}T',
                       'levels': {'D': logging.DEBUG,
                                  'I': logging.INFO,
                                  'W': logging.WARNING,
                                  'E': logging.ERROR,
                                  'F': logging.FATAL
                                  }
                       },
              'syslog': {'regex': ('[0-9-]{10}T[0-9:]{8}Z (?P<level>'
                                   'debug|info|notice|warning|err|crit|'
                                   'alert|emerg)'),
                         'levels': {'debug': logging.DEBUG,
                                    'info': logging.INFO,
                                    'notice': logging.NOTICE,
                                    'warning': logging.WARNING,
                                    'err': logging.ERROR,
                                    'crit': logging.CRITICAL,
                                    'alert': logging.ALERT,
                                    'emerg': logging.EMERG
                                    }
                         },
              'anaconda': {'regex': ('[0-9:]{8},[0-9]+ (?P<level>'
                                     'DEBUG|INFO|WARNING|ERROR|CRITICAL)'),
                           'levels': {'DEBUG': logging.DEBUG,
                                      'INFO': logging.INFO,
                                      'WARNING': logging.WARNING,
                                      'ERROR': logging.ERROR,
                                      'CRITICAL': logging.CRITICAL
                                      }
                           },
              'netprobe': {'regex': ('[0-9-]{10} [0-9:]{8},[0-9]+ (?P<level>'
                                     'DEBUG|INFO|WARNING|ERROR|CRITICAL)'),
                           'levels': {'DEBUG': logging.DEBUG,
                                      'INFO': logging.INFO,
                                      'WARNING': logging.WARNING,
                                      'ERROR': logging.ERROR,
                                      'CRITICAL': logging.CRITICAL
                                      }
                           }

              }
relevel_errors = {
    'anaconda': [
        {
            'regex': 'Error downloading \
http://.*/images/(product|updates).img: HTTP response code said error',
            'levelfrom': logging.ERROR,
            'levelto': logging.WARNING
        },
        {
            'regex': 'got to setupCdrom without a CD device',
            'levelfrom': logging.ERROR,
            'levelto': logging.WARNING
        }
    ]
}
# Create a main logger.
logging.basicConfig(format='%(levelname)s: %(message)s')
main_logger = logging.getLogger()
main_logger.setLevel(logging.NOTSET)


class WatchedFile:
    """WatchedFile(filename) => Object that read lines from file if exist."""

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
        """Return list of last append lines from file if exist."""

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


class WatchedGroup:
    """Can send data from group of specified files to specified servers."""

    def __init__(self, servers, files, name):
        self.servers = servers
        self.files = files
        self.log_type = files.get('log_type', 'syslog')
        self.name = name
        self._createLogger()

    def _createLogger(self):
        self.watchedfiles = []
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.NOTSET)
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
        """Send append data from files to servers."""

        for watchedfile in self.watchedfiles:
            for line in watchedfile.readLines():
                line = line.strip()
                level = self._get_msg_level(line, self.log_type)
                # Get rid of duplicated information in anaconda logs
                line = re.sub(
                    msg_levels[self.log_type]['regex'] + "\s*:?\s?",
                    "",
                    line
                )
                # Ignore meaningless errors
                try:
                    for r in relevel_errors[self.log_type]:
                        if level == r['levelfrom'] and \
                                re.match(r['regex'], line):
                            level = r['levelto']
                except KeyError:
                    pass
                self.logger.log(level, line)
                main_logger and main_logger.log(
                    level,
                    'From file "%s" send: %s' % (watchedfile.name, line)
                )

    @staticmethod
    def _get_msg_level(line, log_type):
        if log_type in msg_levels:
            msg_type = msg_levels[log_type]
            regex = re.match(msg_type['regex'], line)
            if regex:
                return msg_type['levels'][regex.group('level')]
        return logging.INFO


def sig_handler(signum, frame):
    """Send all new data when signal arrived."""

    if not sending_in_progress:
        send_all()
        exit(signum)
    else:
        config['run_once'] = True


def send_all():
    """Send any updates."""

    for group in watchlist:
        group.send()


def main_loop():
    """Periodicaly call sendlogs() for each group in watchlist."""

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    while watchlist:
        time.sleep(0.5)
        send_all()
        # If asked to run_once, exit now
        if config['run_once']:
            break


class Config:
    """Collection of config generation methods.
    Usage: config = Config.getConfig()
    """

    @classmethod
    def getConfig(cls):
        """Generate config from command line arguments and config file."""

        # example_config = {
        #       "daemon": True,
        #       "run_once": False,
        #       "debug": False,
        #       "watchlist": [
        #           {"servers": [ {"host": "localhost", "port": 514} ],
        #            "watchfiles": [
        #               {"tag": "anaconda",
        #                "log_type": "anaconda",
        #                "files": ["/tmp/anaconda.log",
        #                   "/mnt/sysimage/root/install.log"]
        #                }
        #               ]
        #            }
        #           ]
        #       }

        default_config = {"daemon": True,
                          "run_once": False,
                          "debug": False,
                          "hostname": cls._getHostname(),
                          "watchlist": []
                          }
        # First use default config as running config.
        config = dict(default_config)
        # Get command line options and validate it.
        cmdline = cls.cmdlineParse()[0]
        # Check config file source and read it.
        if cmdline.config_file or cmdline.stdin_config:
            try:
                if cmdline.stdin_config is True:
                    fo = sys.stdin
                else:
                    fo = open(cmdline.config_file, 'r')
                parsed_config = json.load(fo)
                if cmdline.debug:
                    print(parsed_config)
            except IOError:  # Raised if IO operations failed.
                main_logger.error("Can not read config file %s\n" %
                                  cmdline.config_file)
                exit(1)
            except ValueError as e:  # Raised if json parsing failed.
                main_logger.error("Can not parse config file. %s\n" %
                                  e.message)
                exit(1)
            #  Validate config from config file.
            cls.configValidate(parsed_config)
            # Copy gathered config from config file to running config
            # structure.
            for key, value in parsed_config.items():
                config[key] = value
        else:
            # If no config file specified use watchlist setting from
            # command line.
            watchlist = {"servers": [{"host": cmdline.host,
                                      "port": cmdline.port}],
                         "watchfiles": [{"tag": cmdline.tag,
                                         "log_type": cmdline.log_type,
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

    @staticmethod
    def _getHostname():
        """Generate hostname by BOOTIF kernel option or use os.uname()."""

        with open('/proc/cmdline') as fo:
            cpu_cmdline = fo.readline().strip()
        regex = re.search('(?<=BOOTIF=)([0-9a-fA-F-]*)', cpu_cmdline)
        if regex:
            mac = regex.group(0).upper()
            return ''.join(mac.split('-'))
        return os.uname()[1]

    @staticmethod
    def cmdlineParse():
        """Parse command line config options."""

        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config_file", metavar="FILE",
                          help="Read config from FILE.")
        parser.add_option("-i", "--stdin", dest="stdin_config", default=False,
                          action="store_true", help="Read config from Stdin.")
        # FIXIT Add optionGroups.
        parser.add_option("-r", "--run-once", dest="run_once",
                          action="store_true", help="Send all data and exit.")
        parser.add_option("-n", "--no-daemon", dest="no_daemon",
                          action="store_true", help="Do not daemonize.")
        parser.add_option("-d", "--debug", dest="debug",
                          action="store_true", help="Print debug messages.")

        parser.add_option("-t", "--tag", dest="tag", metavar="TAG",
                          help="Set tag of sending messages as TAG.")
        parser.add_option("-T", "--type", dest="log_type", metavar="TYPE",
                          default='syslog',
                          help="Set type of files as TYPE"
                               "(default: %default).")
        parser.add_option("-f", "--watchfile", dest="watchfiles",
                          action="append",
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
                                " --tag, --watchfile, --type,"
                                " --host and --port will be ignored.")
        if (not (options.config_file or options.stdin_config) and
                not (options.tag and options.watchfiles and options.host)):
            parser.error("Options --tag, --watchfile and --host"
                         " must be set up at the same time.")
            exit(1)
        return options, args

    @staticmethod
    def _checkType(value, value_type, value_name='', msg=None):
        """Check correctness of type of value and exit if not."""

        if not isinstance(value, value_type):
            message = msg or "Value %r in config have type %r but"\
                " %r is expected." %\
                (value_name, type(value).__name__, value_type.__name__)
            main_logger.error(message)
            exit(1)

    @classmethod
    def configValidate(cls, config):
        """Validate types and names of data items in config."""

        cls._checkType(config, dict, msg='Config must be a dict.')
        for key in ("daemon", "run_once", "debug"):
            if key in config:
                cls._checkType(config[key], bool, key)
        key = "hostname"
        if key in config:
            cls._checkType(config[key], basestring, key)

        key = "watchlist"
        if key in config:
            cls._checkType(config[key], list, key)
        else:
            main_logger.error("There must be key %r in config." % key)
            exit(1)

        for item in config["watchlist"]:
            cls._checkType(item, dict, "watchlist[n]")
            key, name = "servers", "watchlist[n]  => servers"
            if key in item:
                cls._checkType(item[key], list, name)
            else:
                main_logger.error("There must be key %r in %s in config." %
                                  (key, '"watchlist[n]" item'))
                exit(1)
            key, name = "watchfiles", "watchlist[n] => watchfiles"
            if key in item:
                cls._checkType(item[key], list, name)
            else:
                main_logger.error("There must be key %r in %s in config." %
                                  (key, '"watchlist[n]" item'))
                exit(1)

            for item2 in item["servers"]:
                cls._checkType(item2, dict, "watchlist[n]  => servers[n]")
                key, name = "host", "watchlist[n]  => servers[n] => host"
                if key in item2:
                    cls._checkType(item2[key], basestring, name)
                else:
                    main_logger.error("There must be key %r in %s in config." %
                                      (key,
                                       '"watchlist[n] => servers[n]" item'))
                    exit(1)
                key, name = "port", "watchlist[n]  => servers[n] => port"
                if key in item2:
                    cls._checkType(item2[key], int, name)

            for item2 in item["watchfiles"]:
                cls._checkType(item2, dict, "watchlist[n]  => watchfiles[n]")
                key, name = "tag", "watchlist[n]  => watchfiles[n] => tag"
                if key in item2:
                    cls._checkType(item2[key], basestring, name)
                else:
                    main_logger.error("There must be key %r in %s in config." %
                                      (key,
                                       '"watchlist[n] => watchfiles[n]" item'))
                    exit(1)
                key = "log_type"
                name = "watchlist[n]  => watchfiles[n] => log_type"
                if key in item2:
                    cls._checkType(item2[key], basestring, name)
                key, name = "files", "watchlist[n]  => watchfiles[n] => files"
                if key in item2:
                    cls._checkType(item2[key], list, name)
                else:
                    main_logger.error("There must be key %r in %s in config." %
                                      (key,
                                       '"watchlist[n] => watchfiles[n]" item'))
                    exit(1)
                for item3 in item2["files"]:
                    name = "watchlist[n]  => watchfiles[n] => files[n]"
                    cls._checkType(item3, basestring, name)


# Create global config.
config = Config.getConfig()
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
