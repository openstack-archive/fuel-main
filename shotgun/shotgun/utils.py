import socket
import re
import os
import shlex
import subprocess

from shotgun.logger import logger


def hostname():
    return socket.gethostname()


def is_ip(name):
    return (re.search(ur"([0-9]{1,3}\.){3}[0-9]{1,3}", name) and True)


def fqdn(name=None):
    if name:
        return socket.getfqdn(name)
    return socket.getfqdn(socket.gethostname())


def is_local(name):
    if name in ("localhost", hostname(), fqdn()):
        return True
    return False


def execute(command, to_filename=None):
    """
    This method is used for running shell commands locally
    and it is able to run series of commands with pipes
    cmd1 | cmd2 | cmd3
    """
    logger.debug("Trying to execute command: %s", command)
    commands = [c.strip() for c in re.split(ur'\|', command)]
    env = os.environ
    env["PATH"] = "/bin:/usr/bin:/sbin:/usr/sbin"

    to_file = None
    if to_filename:
        to_file = open(to_filename, 'wb')

    process = []
    for c in commands:
        try:
            process.append(subprocess.Popen(
                shlex.split(c),
                env=env,
                stdin=(process[-1].stdout if process else None),
                stdout=(to_file
                        if (len(process) == len(commands) - 1) and to_file
                        else subprocess.PIPE),
                stderr=(subprocess.PIPE)
            ))
        except OSError as e:
            return (1, "", "%s\n" % str(e))

        if len(process) >= 2:
            process[-2].stdout.close()
    stdout, stderr = process[-1].communicate()
    return (process[-1].returncode, stdout, stderr)
