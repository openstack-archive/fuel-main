from provision import ProvisionException
from provision import ProvisionAlreadyExists, ProvisionDoesNotExist
from provision import Provision
import logging
import xmlrpclib

class Cobbler(Provision):
    def __init__(self, config):
        self.logger = logging.getLogger('provision.cobbler')
        try:
            self.url = config.url
            self.user = config.user
            self.password = config.password
        except AttributeError as e:
            self.logger.error('Provision configuration error. Not all necessary attributes are set properly.')
            raise e

        self.logger.debug('Cobbler config: url="%s", user="%s", password="%s"' % (self.url, self.user, self.password))

        try:
            self.server = xmlrpclib.Server(self.url)
            self.token = self.server.login(self.user, self.password)
        except ProvisionException as e:
            self.logger.error('Error occured while connecting to provision server.')
            raise e

    def _get_any_profile(self):
        profiles = self.server.get_profiles(self.token)
        if profiles:
            return profiles[0]
        raise ProvisionException, "There is no available profiles"

    def system_by_name(self, name):
        systems = self.server.find_system({'name':name}, self.token)
        if systems:
            if len(systems) > 1:
                self.logger.error("There are more than one system found by pattern: %s" % name)
                raise ProvisionException, "There are more than one system found by pattern: %s" % name
            return systems[0]
        return None

    # FIXME
    # IT NEEDED TO BE IMPLEMENTED AS ONLY METHOD FOR ADD AND EDIT
    def add_system(self, name, mac, profile, kopts=""):
        if self.system_by_name(name):
            self.logger.error("Trying to add system that already exists: %s" % name)
            raise ProvisionAlreadyExists, "System with name %s already exists. Try to edit it." % name
        system_id = self.server.new_system(self.token)
        self.server.modify_system(system_id, 'name', name, self.token)
        self.server.modify_system(system_id, 'profile', profile.name, self.token)
        self.server.modify_system(system_id, 'kopts', kopts, self.token)
        self.server.modify_system(system_id, 'modify_interface', {
                "macaddress-eth0": mac,
                }, self.token)
        self.server.modify_system(system_id, 'power_type', power.power_type, self.token)
        if power.power_user:
            self.server.modify_system(system_id, 'power_user', power.power_user, self.token)
        if power.power_pass:
            self.server.modify_system(system_id, 'power_pass', power.power_pass, self.token)
        if power.power_id:
            self.server.modify_system(system_id, 'power_id', power.power_id, self.token)
        if power.power_address:
            self.server.modify_system(system_id, 'power_address', power.power_address, self.token)
        self.server.save_system(system_id, self.token)
        return self.system_by_name(name)

    def edit_system(self, name, mac, power, profile, kopts=""):
        if not self.system_by_name(name):
            self.logger.error("Trying to edit system that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "System with name %s does not exist. Try to edit it." % name
        system_id = self.server.get_system_handle(name, self.token)
        self.server.modify_system(system_id, 'profile', profile.name, self.token)
        self.server.modify_system(system_id, 'kopts', kopts, self.token)
        self.server.modify_system(system_id, 'modify_interface', {
                "macaddress-eth0": mac,
                }, self.token)

        self.server.modify_system(system_id, 'power_type', power.power_type, self.token)
        if power.power_user:
            self.server.modify_system(system_id, 'power_user', power.power_user, self.token)
        if power.power_pass:
            self.server.modify_system(system_id, 'power_pass', power.power_pass, self.token)
        if power.power_id:
            self.server.modify_system(system_id, 'power_id', power.power_id, self.token)
        if power.power_address:
            self.server.modify_system(system_id, 'power_address', power.power_address, self.token)
        self.server.save_system(system_id, self.token)
        return self.system_by_name(name)

    def power_system(self, name, power):
        if not self.system_by_name(name):
            self.logger.error("Trying to power system that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "System with name %s does not exist. Try to edit it." % name
        if power not in ('on', 'off', 'reboot', 'status'):
            raise ValueError, "Power has invalid value"
        system_id = self.server.get_system_handle(name, self.token)
        self.server.power_system(system_handle, power, self.token)
        return self.system_by_name(name)

    def handle_system(self, name, mac, power, profile, kopts=""):
        try:
            self.edit_system(name, mac, power, profile, kopts)
            self.logger.info("Edited system: %s" % name)
        except ProvisionDoesNotExist:
            self.add_system(name, mac, power, profile, kopts)
            self.logger.info("Added system: %s" % name)


    def del_system(self, name):
        system = self.system_by_name(name)
        if not system:
            self.logger.error("Trying to remove system that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "There is no system with name %s" % name
        self.server.remove_system(name, self.token)
        self.logger.info("Removed system %s" % name)

    def profile_by_name(self, name):
        profiles = self.server.find_profile({'name':name}, self.token)
        if profiles:
            if len(profiles) > 1:
                self.logger.error("There are more than one profile found by pattern: %s" % name)
                raise ProvisionException, "There are more than one profile found by pattern: %s" % name
            return profiles[0]
        return None

    # FIXME
    # IT NEEDED TO BE IMPLEMENTED AS ONLY METHOD FOR ADD AND EDIT
    def add_profile(self, name, distro, kickstart):
        if self.profile_by_name(name):
            self.logger.error("Trying to add profile that already exists: %s" % name)
            raise ProvisionAlreadyExists, "Profile with name %s already exists. Try to edit it." % name
        profile_id = self.server.new_profile(self.token)
        self.server.modify_profile(profile_id, 'name', name, self.token)
        self.server.modify_profile(profile_id, 'distro', distro, self.token)
        self.server.modify_profile(profile_id, 'kickstart', kickstart, self.token)
        self.server.save_profile(profile_id, self.token)
        return self.profile_by_name(name)

    def edit_profile(self, name, distro, kickstart):
        if not self.profile_by_name(name):
            self.logger.error("Trying to edit profile that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "Profile with name %s does not exist. Try to add it." % name
        profile_id = self.server.get_profile_handle(name, self.token)
        self.server.modify_profile(profile_id, 'distro', distro, self.token)
        self.server.modify_profile(profile_id, 'kickstart', kickstart, self.token)
        self.server.save_profile(profile_id, self.token)
        return self.profile_by_name(name)

    def handle_profile(self, name, distro, seed):
        try:
            self.edit_profile(name, distro, seed)
            self.logger.info("Edited profile: %s" % name)
        except ProvisionDoesNotExist:
            self.add_profile(name, distro, seed)
            self.logger.info("Added profile: %s" % name)

    def del_profile(self, name):
        profile = self.profile_by_name(name)
        if not profile:
            self.logger.error("Trying to remove profile that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "There is no profile with name %s" % name
        self.server.remove_profile(name, self.token)
        self.logger.info("Removed profile: %s" % name)

    def distro_by_name(self, name):
        distros = self.server.find_distro({'name':name}, self.token)
        if distros:
            if len(distros) > 1:
                self.logger.error("There are more than one distro found by pattern: %s" % name)
                raise ProvisionException, "There are more than one distro found by pattern %s" % name
            return distros[0]
        return None

    # FIXME
    # IT NEEDED TO BE IMPLEMENTED AS ONLY METHOD FOR ADD AND EDIT
    def add_distro(self, name, kernel, initrd, arch, breed, osversion):
        if self.distro_by_name(name):
            self.logger.error("Trying to add distro that already exists: %s" % name)
            raise ProvisionAlreadyExists, "Distro with name %s already exists. Try to edit it." % name
        distro_id = self.server.new_distro(self.token)
        self.server.modify_distro(distro_id, 'name', name, self.token)
        self.server.modify_distro(distro_id, 'kernel', kernel, self.token)
        self.server.modify_distro(distro_id, 'initrd', initrd, self.token)
        self.server.modify_distro(distro_id, 'arch', arch, self.token)
        self.server.modify_distro(distro_id, 'breed', breed, self.token)
        self.server.modify_distro(distro_id, 'os_version', osversion, self.token)
        self.server.save_distro(distro_id, self.token)
        return self.distro_by_name(name)

    def edit_distro(self, name, kernel, initrd, arch, breed, osversion):
        if not self.distro_by_name(name):
            self.logger.error("Trying to edit distro that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "Distro with name %s does not exist. Try to add it." % name
        distro_id = self.server.get_distro_handle(name, self.token)
        self.server.modify_distro(distro_id, 'kernel', kernel, self.token)
        self.server.modify_distro(distro_id, 'initrd', initrd, self.token)
        self.server.modify_distro(distro_id, 'arch', arch, self.token)
        self.server.modify_distro(distro_id, 'breed', breed, self.token)
        self.server.modify_distro(distro_id, 'os_version', osversion, self.token)
        self.server.save_distro(distro_id, self.token)
        return self.distro_by_name(name)

    def handle_distro(self, name, kernel, initrd, arch, os, osversion):
        try:
            self.edit_distro(name, kernel, initrd, arch, os, osversion)
            self.logger.info("Edited distro: %s" % name)
        except ProvisionDoesNotExist:
            self.add_distro(name, kernel, initrd, arch, os, osversion)
            self.logger.info("Added distro: %s" % name)
        

    def del_distro(self, name):
        distro = self.distro_by_name(name)
        if not distro:
            self.logger.error("Trying to remove distro that does not exist: %s" % name)
            raise ProvisionDoesNotExist, "There is no distro with name %s" % name
        self.server.remove_distro(name, self.token)
        self.logger.info("Removed distro %s" % name)

    # API

    def save_profile(self, profile):
        self.handle_distro(profile.name, 
                           profile.kernel, 
                           profile.initrd, 
                           profile.arch, 
                           profile.os, 
                           profile.osversion)
        self.handle_profile(profile.name, 
                            profile.name, 
                            profile.seed)


    def save_node(self, node):
        self.handle_system(node.name,
                           node.mac,
                           node.power,
                           node.profile,
                           node.kopts,
                           )

    def power_on(self, node):
        self.power_system(node.name, 'on')

    def power_off(self, node):
        self.power_system(node.name, 'off')

    def power_reboot(self, node):
        self.power_system(node.name, 'reboot')

    def power_status(self, node):
        raise NotImplementedError
