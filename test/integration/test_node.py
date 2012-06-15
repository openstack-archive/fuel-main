import shlex
import os
import logging
import time
from subprocess import Popen, PIPE

from . import ci
from devops.helpers import wait, tcp_ping, http

import paramiko

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

def read_until(channel, end, log=None):
    buff = ""
    while not buff.endswith(end):
        resp = channel.recv(9999)
        buff += resp
    if log:
        log.write(buff)
    return buff

class TestNode(object):
    def test_install_cookbook(self):
        # TODO: all in one ssh session
        host = str(ci.environment.node['admin'].ip_address)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username="ubuntu", password="r00tme")

        sample_path = os.path.join("..", "scripts", "ci")
        sample_remote_path = "/home/ubuntu"

        # removing old cookbook
        (sin, sout, serr) = ssh.exec_command(
            "rm -rf %s" % os.path.join(sample_remote_path, "sample-cook")
        )
        
        sftp = ssh.open_sftp()
        sftp.put(
            os.path.join(sample_path, "sample-release.json"),
            os.path.join(sample_remote_path, "sample-release.json")
        )

        for root, dirs, fls in os.walk(os.path.join(sample_path, "sample-cook")):
            curdir = os.path.join(
                sample_remote_path,
                os.path.relpath(root, sample_path)
            )
            sftp.mkdir(curdir)

            for fl in fls:
                sftp.put(
                    os.path.join(root, fl),
                    os.path.join(curdir, fl)
                )

        sftp.close()

        commands = [
            "rm -rf /opt/nailgun/nailgun.sqlite",
            "source /opt/nailgun-venv/bin/activate",
            "python /opt/nailgun/manage.py syncdb --noinput",
            "deactivate",
            "/opt/nailgun/bin/install_cookbook %s" % os.path.join(sample_remote_path, "sample-cook"),
            "/opt/nailgun/bin/create_release %s" % os.path.join(sample_remote_path, "sample-release.json"),
            # ...
        ]

        chan = ssh.invoke_shell()

        chan.send("sudo -s\n")
        read_until(chan, "ubuntu: ")
        chan.send("r00tme\n")
        read_until(chan, "# ")

        for cmd in commands:
            print "~$ %s" % cmd
            chan.send(cmd+"\n")
            #with open("log.html", "a+") as l:
            #    read_until(chan, "# ", log=l)
            read_until(chan, "# ")
        
        ssh.close()