from __future__ import absolute_import

import logging
import xmlrpclib

from .utils import get_fields


class Cobbler:

    aliases = {
        'ks_meta': ['ksmeta'],
        'mac_address': ['mac'],
        'ip_address': ['ip'],
    }

    def __init__(self, cobbler_api_url, username, password):
        self.logger = logging.getLogger('provision.cobbler')
        try:
            self.remote = xmlrpclib.Server(cobbler_api_url, allow_none=True)
            self.token = self.remote.login(username, password)
        except Exception as e:
            self.logger.error('Error while connecting to cobbler api: %s' % e)
            raise e

    def item_from_dict(self, what, obj_name, obj_dict, lazy=True, ilazy=False):
        item_fields = get_fields(what)
        self.logger.debug("Valid item fields: %s" % item_fields['fields'])
        if what == 'system':
            self.logger.debug("Valid interface fields: %s" %
                              item_fields['interface_fields'])

        # converting interfaces extra parameters into ks_meta format
        int_extra_str = ''
        for iname in obj_dict.get('interfaces_extra', {}):
            int_extra_dict = obj_dict['interfaces_extra'][iname]
            for int_extra in int_extra_dict:
                int_extra_str = """%s interface_extra_%s_%s=%s""" % \
                    (int_extra_str, iname, int_extra,
                     int_extra_dict[int_extra])

        item_dict = {}
        for opt in obj_dict:

            # detecting aliased options and substituting them with orig options
            opt = opt.replace('-', '_')
            for orig_opt in self.aliases:
                if opt in self.aliases[orig_opt]:
                    opt = orig_opt
                    break

            # checking if option is valid cobbler option
            if not opt in item_fields['fields']:
                self.logger.debug('Skipping %s field: %s' % (what, opt))
                continue

            # extending ks_meta option with extra parameters
            if opt == 'ks_meta':
                ks_meta = '%s %s' % (obj_dict[opt], int_extra_str)
                item_dict[opt] = ks_meta
                continue

            item_dict[opt] = obj_dict[opt]

        # special handling for system interface fields
        # which are the only objects in cobbler that will ever work this way
        if what == 'system' and 'interfaces' in obj_dict:
            interfaces_names = set([])
            interfaces_item_dict = {}
            for iname in obj_dict['interfaces']:
                idict = obj_dict['interfaces'][iname]
                for iopt in idict:
                    if not iopt in item_fields['interface_fields']:
                        self.logger.debug('Skipping interface opt: %s' % iopt)
                        continue
                    interfaces_names.add(iname)
                    interfaces_item_dict['%s-%s' % (iopt, iname)] = idict[iopt]

        # Here we assume that the item fully qualified by item_dict
        # lazy parameter is set to False.
        # So in order to prevent not defined fields to have non default
        # values we need to delete item at first and then to create it
        # initializing it from obj_dict.
        if not lazy and self.remote.has_item(what, obj_name):
            self.logger.debug('Lazy mode is disabled, removing %s: %s' %
                              (what, obj_name))
            self.remote.remove_item(what, obj_name, self.token)

        if self.remote.has_item(what, obj_name):
            self.logger.debug('Getting %s handle: %s' % (what, obj_name))
            item_id = self.remote.get_item_handle(what, obj_name, self.token)
        else:
            self.logger.debug('Creating new %s: %s' % (what, obj_name))
            item_id = self.remote.new_item(what, self.token)
            self.remote.modify_item(what, item_id,
                                    'name', obj_name, self.token)

        # defining all item options
        for opt in item_dict:
            self.logger.debug('Setting %s %s opt: %s = %s' %
                              (what, obj_name, opt, item_dict[opt]))
            self.remote.modify_item(what, item_id,
                                    opt, item_dict[opt], self.token)

        # removing all system interfaces if ilazy mode is disabled
        if what == 'system' and not ilazy:
            try:
                system = self.remote.get_item('system', obj_name)
                ifaces = system.get('interfaces', {})
            except:
                pass
            else:
                for iname in ifaces:
                    if not iname in interfaces_names:
                        self.logger.debug('Ilazy mode is disabled, '
                                          'removing interface: %s' % iname)
                        self.remote.modify_system(item_id, 'delete_interface',
                                                  iname, self.token)

        # defining system interfaces
        if what == 'system':
            self.logger.debug('Defining system %s interfaces: %s' %
                              (obj_name, interfaces_item_dict))
            self.remote.modify_system(item_id, 'modify_interface',
                                      interfaces_item_dict, self.token)

        self.logger.debug('Saving %s %s' % (what, obj_name))
        self.remote.save_item(what, item_id, self.token)

    def system_from_dict(self, obj_name, obj_dict, lazy=True):
        return self.item_from_dict('system', obj_name, obj_dict)

    def _item_id_if_exists(self, what, obj_name):
        try:
            if self.remote.has_item(what, obj_name):
                return self.remote.get_item_handle(what, obj_name, self.token)
        except:
            pass
        return None

    def power(self, obj_name, power):
        system_id = _item_id_if_exists('system', obj_name)
        if not system_id is None:
            self.remote.power_system(system_id, power, self.token)
        else:
            raise Exception('There is no system named: %s' % obj_name)

    def power_on(self, obj_name):
        self.power(obj_name, 'on')

    def power_reboot(self, obj_name):
        self.power(obj_name, 'reboot')
