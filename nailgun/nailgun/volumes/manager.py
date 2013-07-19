# -*- coding: utf-8 -*-

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

'''
Classes for working with disks and volumes.
All sizes in megabytes.
'''

import json

from nailgun.logger import logger
from nailgun.errors import errors


def only_disks(spaces):
    '''
    Helper for retrieving only disks from spaces
    '''
    return filter(lambda space: space['type'] == 'disk', spaces)


def only_vg(spaces):
    '''
    Helper for retrieving only volumes groups from spaces
    '''
    return filter(lambda space: space['type'] == 'vg', spaces)


def gb_to_mb(gb):
    '''
    Convert gigabytes to megabytes
    '''
    return int(gb * 1024)


def byte_to_megabyte(byte):
    '''
    Convert bytes to megabytes
    '''
    return byte / 1024 ** 2


class DisksFormatConvertor(object):
    '''
    Class converts format from `simple` in which we
    communicate with UI to `full` in which we store
    data about disks\volumes in database, send to
    orchestrator and vice versa.

    Full disk format example:
        [
            {
                "type": "disk",
                "id": "sda",
                "size": 953869,
                "volumes": [
                    {
                        "mount": "/boot",
                        "type": "raid",
                        "size": 200
                    },
                    .....
                    {
                        "size": 938905,
                        "type": "pv",
                        "vg": "os"
                    }
                ]
            }
        ]

    Simple disk format example:
        [
            {
                "id": "sda",
                "size": 953869,
                "volumes": [
                    {
                        "name": "os",
                        "size": 938905,
                    }
                ]
            }
        ]
    '''

    @classmethod
    def format_disks_to_full(cls, node, disks):
        '''
        convert disks from simple format to full format
        '''
        full_format = []
        for disk in disks:
            for volume in disk['volumes']:
                full_format = node.volume_manager.set_volume_size(
                    disk['id'], volume['name'], volume['size'])

        return full_format

    @classmethod
    def format_disks_to_simple(cls, full):
        '''
        convert disks from full format to simple format
        '''
        disks_in_simple_format = []

        # retrieve only phisical disks
        disks_full_format = only_disks(full)

        for disk in disks_full_format:
            reserve_size = cls.calculate_service_partitions_size(
                disk['volumes'])
            size = 0
            if disk['size'] >= reserve_size:
                size = disk['size'] - reserve_size

            disk_simple = {
                'id': disk['id'],
                'size': size,
                'volumes': cls.format_volumes_to_simple(disk['volumes'])}

            disks_in_simple_format.append(disk_simple)

        return disks_in_simple_format

    @classmethod
    def calculate_service_partitions_size(self, volumes):
        not_vg_partitions = filter(lambda vg: vg.get('type') != 'pv', volumes)
        return sum(
            [partition.get('size', 0) for partition in not_vg_partitions])

    @classmethod
    def format_volumes_to_simple(cls, all_partitions):
        '''
        convert volumes from full format to simple format
        '''
        pv_full_format = filter(
            lambda vg: vg.get('type') == 'pv', all_partitions)

        volumes_simple_format = []
        for volume in pv_full_format:
            volume_simple = {
                'name': volume['vg'],
                'size': volume['size']}

            volumes_simple_format.append(volume_simple)

        return volumes_simple_format

    @classmethod
    def get_volumes_info(cls, node):
        '''
        Return volumes info for node

        :returns: [
                {
                    "name": "os",
                    "label": "Base System",
                    "minimum": 100002
                }
            ]
        '''
        try:
            volumes_ids = node.cluster.release.volumes_metadata[
                'volumes_roles_mapping'][node.role]
        except KeyError:
            raise errors.CannotFindVolumesInfoForRole()

        volumes_info = []
        for volume_id in volumes_ids:
            volume = filter(
                lambda volume: volume.get('id') == volume_id,
                node.cluster.release.volumes_metadata['volumes'])[0]

            # Here we calculate min_size of nodes
            min_size = node.volume_manager.expand_generators(
                volume)['min_size']

            volumes_info.append({
                'name': volume_id,
                'label': volume['label'],
                'min_size': min_size})

        return volumes_info


class Disk(object):

    def __init__(self, generator_method, disk_id, size, boot_is_raid=True):
        self.call_generator = generator_method
        self.id = disk_id
        self.size = size
        self.free_space = size
        self.volumes = []

        # For determination type of boot
        self.boot_is_raid = boot_is_raid

        # For each disk we need to create
        # service partitions and reserve space
        self.create_service_partitions()

    def create_service_partitions(self):
        self.create_boot_records()
        self.create_boot_partition()

    def service_partitions_size(self):
        return self.call_generator('calc_boot_size') + \
            self.call_generator('calc_boot_records_size')

    def create_boot_partition(self):
        boot_size = self.call_generator('calc_boot_size')
        size = boot_size if self.free_space >= boot_size else 0

        partition_type = 'partition'
        if self.boot_is_raid:
            partition_type = 'raid'

        self.volumes.append({
            'type': partition_type,
            'mount': '/boot',
            'size': size})
        self.free_space -= size

    def create_boot_records(self):
        '''
        Reserve space for efi, gpt, bios
        '''
        boot_records_size = self.call_generator('calc_boot_records_size')
        size = boot_records_size if self.free_space >= boot_records_size else 0
        self.volumes.append({'type': 'boot', 'size': size})
        self.free_space -= size

    def create_lvm_meta(self, name):
        logger.debug('Appending lvm meta to volumee.')
        lvm_meta_size = self.call_generator('calc_lvm_meta_size')
        size = lvm_meta_size if self.free_space >= lvm_meta_size else 0
        self.volumes.append({'type': 'lvm_meta', 'size': size, 'name': name})
        self.free_space -= size

    def create_pv(self, name, size=None):
        '''
        Allocates all available space if
        size is None
        '''
        logger.debug('Creating or updating PV: disk=%s vg=%s, size=%s',
                     self.id, name, str(size))

        self.create_lvm_meta(name)

        if size is None:
            logger.debug(
                'Size is not defined. Will use all free space on this disk.')
            size = self.free_space

        self.free_space -= size
        logger.debug('Appending PV to volumes.')
        self.volumes.append({
            'type': 'pv',
            'vg': name,
            'size': size})

    def clear(self):
        self.volumes = []
        self.free_space = self.size

    def reset(self):
        self.clear()
        self.create_service_partitions()

    def render(self):
        return {
            "id": self.id,
            "type": "disk",
            "size": self.size,
            "volumes": self.volumes
        }

    def __repr__(self):
        return json.dumps(self.render())

    def __str__(self):
        return json.dumps(self.render(), indent=4)


class VolumeManager(object):
    def __init__(self, node):
        '''
        Disks and volumes will be set according to node
        attributes.
        '''
        logger.debug("VolumeManager initialized with node: %s", node.id)
        self.disks = []
        self.volumes = []
        self.node = node
        self.volumes = self.node.attributes.volumes or []

        for d in sorted(self.node.meta["disks"], key=lambda i: i["name"]):
            disks_count = len(self.node.meta["disks"])
            boot_is_raid = True if disks_count > 1 else False

            disk = Disk(
                self.call_generator, d["disk"],
                byte_to_megabyte(d["size"]),
                boot_is_raid=boot_is_raid)

            for v in only_disks(self.volumes):
                if v.get('id') == disk.id:
                    disk.volumes = v.get('volumes', [])

            self.disks.append(disk)

        logger.debug("VolumeManager: volumes: %s", self.volumes)
        logger.debug("VolumeManager: disks: %s", self.disks)

    def set_volume_size(self, disk_id, volume_name, size):
        disk = filter(
            lambda volume: volume['id'] == disk_id,
            only_disks(self.volumes))[0]

        volume = filter(
            lambda volume: volume_name == volume.get('vg'),
            disk['volumes'])[0]
        if disk['size'] >= size:
            volume['size'] = size

        # Recalculate sizes of volume groups
        volumes_metadata = self.node.cluster.release.volumes_metadata[
            'volumes']
        for index, volume in enumerate(self.volumes):
            if volume.get('type') != 'vg':
                continue

            vg_id = volume.get('id')
            vg_template = filter(
                lambda volume: volume.get('id') == vg_id,
                volumes_metadata)[0]

            self.volumes[index] = self.expand_generators(vg_template)

        return self.volumes

    def call_generator(self, generator, *args):
        generators = {
            # Calculate swap space based on total RAM
            'calc_swap_size': self._calc_swap_size,
            # root = 10GB
            'calc_root_size': lambda: gb_to_mb(10),
            # boot = 200MB
            'calc_boot_size': lambda: 200,
            # boot records size = 300MB
            'calc_boot_records_size': lambda: 300,
            # let's think that size of mbr is 10MB
            'calc_mbr_size': lambda: 10,
            # lvm meta = 64MB for one volume group
            'calc_lvm_meta_size': lambda: 64,
            'calc_total_vg': self._calc_total_vg,
            # virtual storage = 5GB
            'calc_min_vm_size': lambda: gb_to_mb(5),
            'calc_min_cinder_size': lambda: gb_to_mb(1.5),
            'calc_total_root_vg': self._calc_total_root_vg}

        generators['calc_os_size'] = \
            lambda: generators['calc_root_size']() + \
            generators['calc_swap_size']()

        generators['calc_os_vg_size'] = generators['calc_os_size']
        generators['calc_min_os_size'] = generators['calc_os_size']

        if not generator in generators:
            raise errors.CannotFindGenerator(
                u'Cannot find generator %s' % generator)

        return generators[generator](*args)

    def _calc_total_root_vg(self):
        return self._calc_total_vg('os') - \
            self.call_generator('calc_swap_size')

    def _calc_total_vg(self, vg):
        logger.debug('_calc_total_vg')
        vg_space = 0
        for v in only_disks(self.volumes):
            for subv in v['volumes']:
                if subv.get('type') == 'pv' and subv.get('vg') == vg:
                    vg_space += subv.get('size', 0)
                elif (subv.get('type') == 'lvm_meta' and
                      subv.get('name') == vg):
                    vg_space -= subv['size']

        return vg_space

    def _calc_swap_size(self):
        '''
        Calc swap size according to RAM

        | RAM          | Recommended swap space      |
        |--------------+-----------------------------|
        | <= 2GB       | 2 times the amount of RAM   |
        | > 2GB – 8GB  | Equal to the amount of RAM  |
        | > 8GB – 64GB | 0.5 times the amount of RAM |
        | > 64GB       | 4GB of swap space           |

        Source https://access.redhat.com/site/documentation/en-US/
                       Red_Hat_Enterprise_Linux/6/html/Installation_Guide/
                       s2-diskpartrecommend-ppc.html#id4394007
        '''
        mem = float(self.node.meta['memory']['total']) / 1024 ** 3
        if mem <= 2:
            return gb_to_mb(int(2 * mem))
        elif mem > 2 and mem <= 8:
            return gb_to_mb(mem)
        elif mem > 8 and mem <= 64:
            return gb_to_mb(int(.5 * mem))
        else:
            return gb_to_mb(4)

    def _allocate_vg(self, name, size=None):
        '''
        Allocate volume group. If size is None,
        then allocate all existing space on all disks.
        '''
        logger.debug('_allocate_vg: vg: %s, size: %s', name, str(size))

        if size is None:
            for disk in self.disks:
                if disk.free_space > 0:
                    logger.debug('Allocating all available space for PV: '
                                 'disk: %s vg: %s', disk.id, name)
                    disk.create_pv(name)
                else:
                    disk.create_pv(name, 0)
        else:
            not_allocated_size = size
            for disk in self.disks:
                logger.debug('Creating PV: disk: %s, vg: %s', disk.id, name)

                if disk.free_space >= not_allocated_size:
                    # if we can allocate all required size
                    # on one disk, then just allocate it
                    size_to_allocation = not_allocated_size
                elif disk.free_space > 0:
                    # if disk has free space, then allocate it
                    size_to_allocation = disk.free_space
                else:
                    # else just allocate pv with size 0
                    size_to_allocation = 0

                disk.create_pv(name, size_to_allocation)
                not_allocated_size -= size_to_allocation

    def gen_volumes_info(self):
        logger.debug(
            u'Generating volumes info for node %s' % self.node.full_name)

        logger.debug('Purging volumes info for all node disks')
        map(lambda d: d.reset(), self.disks)
        self.volumes = [d.render() for d in self.disks]

        role = self.node.role
        if not self.node.cluster:
            return self.volumes

        self.volumes.extend(self.get_volumes_groups_for_role(role))

        volumes_metadata = self.node.cluster.release.volumes_metadata
        vg_names_for_role = volumes_metadata['volumes_roles_mapping'][role]
        for vg_name in vg_names_for_role:
            # For last volume group in 'volumes_roles_mapping' list
            # we allocates all free space
            if len(vg_names_for_role) == 1 or vg_name == vg_names_for_role[-1]:
                self._allocate_vg(vg_name)
            else:
                volume_meta = filter(
                    lambda volume: volume.get('id') == vg_name,
                    volumes_metadata['volumes'])[0]
                min_size = self.expand_generators(volume_meta)['min_size']

                self._allocate_vg(vg_name, min_size)

        self.volumes = self.expand_generators(self.volumes)
        return self.volumes

    def get_volumes_groups_for_role(self, role):
        volumes_metadata = self.node.cluster.release.volumes_metadata
        volume_groups_for_role = volumes_metadata[
            'volumes_roles_mapping'][role]

        return filter(
            lambda vg: vg.get('id') in volume_groups_for_role,
            volumes_metadata['volumes'])

    def expand_generators(self, cdict):
        new_dict = {}
        if isinstance(cdict, dict):
            for i, val in cdict.iteritems():
                if type(val) in (str, unicode, int, float):
                    new_dict[i] = val
                elif isinstance(val, dict):
                    if "generator" in val:
                        logger.debug("Generating value: generator: %s "
                                     "generator_args: %s", val["generator"],
                                     val.get("generator_args", []))
                        genval = self.call_generator(
                            val["generator"],
                            *(val.get("generator_args", []))
                        )
                        logger.debug("Generated value: %s", str(genval))
                        new_dict[i] = genval
                    else:
                        new_dict[i] = self.expand_generators(val)
                elif isinstance(val, list):
                    new_dict[i] = []
                    for d in val:
                        new_dict[i].append(self.expand_generators(d))
        elif isinstance(cdict, list):
            new_dict = []
            for d in cdict:
                new_dict.append(self.expand_generators(d))
        return new_dict

    def check_disk_space_for_deployment(self):
        '''
        Check disks space for minimal installation.
        This method calls in before deployment task.

        :raises: errors.NotEnoughFreeSpace
        '''
        disks_space = sum([d.size for d in self.disks])
        minimal_installation_size = self.__calc_minimal_installation_size()

        if disks_space < minimal_installation_size:
            raise errors.NotEnoughFreeSpace(
                u"Node '%s' has insufficient disk space" %
                self.node.human_readable_name)

    def __calc_minimal_installation_size(self):
        '''
        Calc minimal installation size depend on node role
        '''
        role = self.node.role
        volumes_metadata = self.node.cluster.release.volumes_metadata
        vg_names_for_role = volumes_metadata['volumes_roles_mapping'][role]

        disks_count = len(filter(lambda disk: disk.size > 0, self.disks))
        boot_size = self.call_generator('calc_boot_size') + \
            self.call_generator('calc_boot_records_size')

        min_installation_size = disks_count * boot_size
        for vg_name in vg_names_for_role:
            volume_meta = filter(
                lambda volume: volume.get('id') == vg_name,
                volumes_metadata['volumes'])[0]
            min_size = self.expand_generators(volume_meta)['min_size']
            min_installation_size += min_size

        return min_installation_size
