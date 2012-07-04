import logging
from provision import ProvisionException
from . import Validator

# server.modify_system(sid, "power_address", "power.example.org", token)
# server.modify_system(sid, "power_type", "ipmitool", token)
# server.modify_system(sid, "power_user", "Admin", token)
# server.modify_system(sid, "power_pass", "magic", token)
# server.modify_system(sid, "power_id", "7", token)

class Power:

    def __init__(self, powertype):
        if Validator.is_powertype_valid(powertype):
            self._type = powertype
        

class PowerEtherWake:
    pass


class PowerLibvirt:
    
    @property
    def virtid(self):
        if not self._virtid:
            raise ProvisionException, "Virtid is not set properly"
        return self._virtid

    @virtid.setter
    def virtid(self, virtid):
        self._virtid = virtid


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
        return self._system("virsh list | grep -q ' %s '" % self.virtid, expected_resultcodes=(0, 1)) == 0

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
            self.logger.debug("Node %s is not running at the moment. Starting." % self.virtid)
            self._virsh("start '%s'", self.virtid)



    def power_of(self):
        if self._is_node_running():
            self.logger.debug("Node %s is running at the moment. Stopping." % node.id)
            self._virsh("destroy '%s'", self.virtid)
            


        

    
