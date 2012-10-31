#!/usr/bin/python

import os
import sys
import string
import logging
from logging.handlers import SysLogHandler
import time

class WatchedFile:
    def __init__(self, fn):
        self.fn = fn
        self.reset()

    def exist(self):
        return os.access(self.fn, os.R_OK)

    def reset(self):
        if self.exist():
            self.fo = open(self.fn, 'r')
        self.where = 0
        self.last_size = 0

    def changed(self):
        if not self.exist(): return 0
        size = os.stat(self.fn)[6]
        if size > self.last_size:
            self.last_size = size
            return 1
        else:
            return 0

    def newStrings(self):
        if not self.exist():
            return ()
        if not getattr(self, 'fo', False):
            self.fo = open(self.fn, 'r')
        self.fo.seek(self.where)
        lines = self.fo.readlines()
        self.where = self.fo.tell()
        return lines

    def close(self):
        self.fo.close()

def main_loop():
    alog = WatchedFile("/tmp/anaconda.log")
    ilog = WatchedFile("/mnt/sysimage/root/install.log")

    # Were we asked to watch specific files?
    watchlist = list()
    if watchfiles:
        # Create WatchedFile objects for each requested file
        for watchfile in watchfiles:
            if os.path.exists(watchfile):
                watchlog = WatchedFile(watchfile)
                watchlist.append(watchlog)

    # Use the default watchlist
    else:
        watchlist = [alog, ilog]

    # Monitor loop
    while 1:
        time.sleep(1)

        # Send any updates
        for wf in watchlist:
            lines = wf.newStrings()
            hostname = checkHostname()
            for line in lines:
                logger.info(line)

        # If asked to run_once, exit now
        if exit:
            break

def checkHostname():
    newhostname = os.uname()[1]
    if hostname != newhostname:
        log_format = '%s %s:%%(message)s' % (newhostname, name)
        formatter = logging.Formatter(log_format)
        syslog.setFormatter(formatter)
        logger.addHandler(syslog)
    return newhostname

# Establish some defaults
name = "anaconda"
server = "localhost"
port = 514
daemon = 1
debug = lambda x,**y: None
watchfiles = []
exit = False

# Process command-line args
n = 0
while n < len(sys.argv):
    arg = sys.argv[n]
    if arg == '--name':
        n = n+1
        name = sys.argv[n]
    elif arg == '--watchfile':
        n = n+1
        watchfiles.extend(sys.argv[n].split(';'))
    elif arg == '--exit':
        exit = True
    elif arg == '--server':
        n = n+1
        server = sys.argv[n]
    elif arg == '--port':
        n = n+1
        port = int(sys.argv[n])
    elif arg == '--debug':
        debug = lambda x,**y: sys.stderr.write(x % y)
    elif arg == '--fg':
        daemon = 0
    n = n+1


# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
syslog = SysLogHandler((server, port))
hostname = os.uname()[1]
log_format = '%s %s:%%(message)s' % (hostname, name)
formatter = logging.Formatter(log_format)
syslog.setFormatter(formatter)
logger.addHandler(syslog)

# Fork and loop
if daemon:
    if not os.fork():
        # Redirect the standard I/O file descriptors to the specified file.
        DEVNULL = getattr(os, "devnull", "/dev/null")
        os.open(DEVNULL, os.O_RDWR) # standard input (0)
        os.dup2(0, 1) # Duplicate standard input to standard output (1)
        os.dup2(0, 2) # Duplicate standard input to standard error (2)

        main_loop()
        sys.exit(1)
    sys.exit(0)
else:
    main_loop()

