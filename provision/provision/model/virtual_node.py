import logging
import re
from node import Node
from . import Validator
from provision import ProvisionException
import subprocess, shlex


class VirtualNode(Node):
    _libvirtname = None

    def __init__(self, name):
        self.logger = logging.getLogger('provision.model.virtualnode')
        self.name = name

    @property
    def libvirtname(self):
        if not self._libvirtname:
            raise ProvisionException, "Libvirtname is not set properly"
        return self._libvirtname

    @libvirtname.setter
    def libvirtname(self, libvirtname):
        self._libvirtname = libvirtname


    # FIXME
    # IT WOULD BE NICE TO INTEGRATE THIS WITH DEVOPS

    def _system(self, command, expected_resultcodes=(0,)):
        self.logger.debug("libvirt: Running %s" % command)

        commands = [ i.strip() for i in re.split(ur'\|', command)]
        serr = []

        process = []
        process.append(subprocess.Popen(shlex.split(commands[0]), stdin=None, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        for c in commands[1:]:
            process.append(subprocess.Popen(shlex.split(c), stdin=process[-1].stdout, 
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

        process[-1].wait()

        for p in process:
            serr += [ err.strip() for err in p.stderr.readlines() ]

        returncode = process[-1].returncode

        if expected_resultcodes and not returncode in expected_resultcodes:
            self.logger.error("libvirt: Command '%s' returned %d, stderr: %s" % (command, returncode, '\n'.join(serr)))
        else:
            self.logger.debug("libvirt: Command '%s' returned %d" % (command, returncode))

        return returncode

    def _is_node_running(self):
        return self._system("virsh list | grep -q ' %s '" % self.libvirtname, expected_resultcodes=(0, 1)) == 0

    def _virsh(self, format, *args):
        command = ("virsh " + format) % args
        self.logger.debug("libvirt: Running '%s'" % command)
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        if process.returncode != 0:
            self.logger.error("libvirt: command '%s' returned code %d:\n%s" % (command, process.returncode, process.stderr.read()))
            raise ProvisionException, "Failed to launch libvirt command '%s'" % command

    def power_on(self):
        if not self._is_node_running():
            self.logger.debug("Node %s is not running at the moment. Starting." % self.libvirtname)
            self._virsh("start '%s'", self.libvirtname)



    def power_of(self):
        if self._is_node_running():
            self.logger.debug("Node %s is running at the moment. Stopping." % node.id)
            self._virsh("destroy '%s'", self.libvirtname)
            
    


