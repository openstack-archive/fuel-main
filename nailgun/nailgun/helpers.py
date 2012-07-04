import logging
import socket

import paramiko


logger = logging.getLogger(__name__)


class SshConnect(object):

    def __init__(self, host, user, keyfile=None, password=None):
        try:
            self.host = host
            self.t = paramiko.Transport((host, 22))
            if password:
                self.t.connect(username=user, password=password)
            elif keyfile:
                self.t.connect(username=user,
                    pkey=paramiko.RSAKey.from_private_key_file(keyfile))

        except:
            self.close()
            raise

    def run(self, cmd, timeout=30):
        logger.debug("[%s] Running command: %s", self.host, cmd)
        chan = self.t.open_session()
        chan.settimeout(timeout)
        chan.exec_command(cmd)
        return chan.recv_exit_status() == 0

    def close(self):
        try:
            if self.t:
                self.t.close()
        except:
            pass
