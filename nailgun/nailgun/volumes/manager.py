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
from copy import deepcopy


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
        volume_manager = node.volume_manager
        for disk in disks:
            for volume in disk['volumes']:
                full_format = volume_manager.set_pv_size(
                    disk['id'], volume['name'], volume['size'])

        return full_format

    @classmethod
    def format_disks_to_simple(cls, full):
        '''
        convert disks from full format to simple format
        '''
        disks_in_simple_format = []

        # retrieve only physical disks
        disks_full_format = only_disks(full)

        for disk in disks_full_format:
            reserved_size = cls.calculate_service_partitions_size(
                disk['volumes'])
            size = 0
            if disk['size'] >= reserved_size:
                size = disk['size'] - reserved_size

            disk_simple = {
                'id': disk['id'],
                'name': disk['name'],
                'size': size,
                'volumes': cls.serialize_pvs(disk['volumes'])}

            disks_in_simple_format.append(disk_simple)

        return disks_in_simple_format

    @classmethod
    def calculate_service_partitions_size(self, volumes):
        not_vg_partitions = filter(lambda vg: vg.get('type') != 'pv', volumes)
        return sum(
            [partition.get('size', 0) for partition in not_vg_partitions])

    @classmethod
    def serialize_pvs(cls, all_partitions):
        '''
        Convert volumes from full format to simple format
        '''
        pv_full_format = filter(
            lambda vg: vg.get('type') == 'pv', all_partitions)

        volumes_simple_format = []
        for volume in pv_full_format:
            calculated_size = volume['size'] - volume['lvm_meta_size']
            size = calculated_size if calculated_size > 0 else 0

            volume_simple = {
                'name': volume['vg'],
                'size': size}

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

    def __init__(self, volumes, generator_method, disk_id, name,
                 size, boot_is_raid=True, possible_pvs_count=0):
        self.call_generator = generator_method
        self.id = disk_id
        self.name = name
        self.size = size
        self.lvm_meta_size = generator_method('calc_lvm_meta_size')
        self.max_lvm_meta_pool_size = self.lvm_meta_size * possible_pvs_count
        self.free_space = self.size
        self.set_volumes(volumes)

        # For determination type of boot
        self.boot_is_raid = boot_is_raid

        # For each disk we need to create
        # service partitions and reserve space
        self.create_service_partitions()

    def set_volumes(self, volumes):
        self.volumes = volumes
        for volume in volumes:
            self.free_space -= volume.get('size', 0)

    def create_service_partitions(self):
        self.create_boot_records()
        self.create_boot_partition()
        self.create_lvm_meta_pool(self.max_lvm_meta_pool_size)

    def create_boot_partition(self):
        boot_size = self.call_generator('calc_boot_size')
        partition_type = 'partition'
        if self.boot_is_raid:
            partition_type = 'raid'

        existing_boot = filter(
            lambda volume: volume.get('mount') == '/boot', self.volumes)

        if not existing_boot:
            self.volumes.append({
                'type': partition_type,
                'mount': '/boot',
                'size': self.get_size(boot_size)})

    def create_boot_records(self):
        '''
        Reserve space for efi, gpt, bios
        '''
        boot_records_size = self.call_generator('calc_boot_records_size')
        existing_boot = filter(
            lambda volume: volume.get('type') == 'boot', self.volumes)

        if not existing_boot:
            self.volumes.append({'type': 'boot', 'size': self.get_size(boot_records_size)})

    def get_size(self, size):
        size_to_allocate = size if self.free_space >= size else 0
        self.free_space -= size_to_allocate
        return size_to_allocate

    def create_lvm_meta_pool(self, size):
        """
        Create lvm pool.
        When new PV will be created, from this pool
        deducated size of single lvm meta for each
        PV on disk.
        """
        existing_lvm_pool = filter(
            lambda volume: volume['type'] == 'lvm_meta_pool', self.volumes)

        if not existing_lvm_pool:
            self.volumes.append({'type': 'lvm_meta_pool', 'size': self.get_size(size)})

    def get_lvm_meta_from_pool(self):
        lvm_meta_pool = filter(
            lambda volume: volume['type'] == 'lvm_meta_pool', self.volumes)[0]

        if lvm_meta_pool['size'] >= self.lvm_meta_size:
            lvm_meta_pool['size'] -= self.lvm_meta_size
            allocated_size = self.lvm_meta_size
        else:
            allocated_size = 0

        return allocated_size

    def put_size_to_lvm_meta_pool(self, size):
        lvm_meta_pool = filter(
            lambda volume: volume['type'] == 'lvm_meta_pool', self.volumes)[0]

        lvm_meta_pool['size'] += size

    def create_pv(self, name, size=None):
        '''
        Allocates all available space if size is None
        Size in parameter should include size of lvm meta
        '''
        logger.debug('Creating or updating PV: disk=%s vg=%s, size=%s',
                     self.id, name, str(size))

        if size is None:
            logger.debug(
                'Size is not defined. Will use all free space on this disk.')
            size = self.free_space

        self.free_space -= size
        # Don't allocate lvm if size equal 0
        lvm_meta_size = self.get_lvm_meta_from_pool() if size else 0

        logger.debug('Appending PV to volumes.')
        self.volumes.append({
            'type': 'pv',
            'vg': name,
            'size': size + lvm_meta_size,
            'lvm_meta_size': lvm_meta_size})

    def remove_pv(self, name):
        """
        Remove PV and return back lvm_meta size to pool
        """
        for i, volume in enumerate(self.volumes[:]):
            if volume.get('type') == 'pv' and volume.get('vg') == name:
                lvm_meta_pool = filter(
                    lambda v: v['type'] == 'lvm_meta_pool', self.volumes)[0]

                # Return back size to lvm_meta_pool
                lvm_meta_pool['size'] += volume['lvm_meta_size']
                # Return back size of PV, without size of lvm meta
                # beacuse we return back size of lvm_meta above
                self.free_space += (volume['size'] - volume['lvm_meta_size'])

                del self.volumes[i]
                break

    def set_pv_size(self, name, size):
        """
        Set PV size
        """
        for volume in self.volumes:
            if volume.get('type') == 'pv' and volume.get('vg') == name:
                # Recreate lvm meta
                self.remove_pv(name)
                self.create_pv(name, size)

    def reset(self):
        self.volumes = []
        self.free_space = self.size
        self.create_service_partitions()

    def render(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': 'disk',
            'size': self.size,
            'volumes': self.volumes,
            'free_space': self.free_space
        }

    def __repr__(self):
        return json.dumps(self.render())

    def __str__(self):
        return json.dumps(self.render(), indent=4)


class VolumeManager(object):
    def __init__(self, node):
        '''
        Disks and volumes will be set according to node attributes.
        VolumeManager should not make any updates in database.
        '''
        # Make sure that we don't change volumes directly from manager
        self.volumes = deepcopy(node.attributes.volumes) or []
        # For swap calculation
        self.ram = node.meta['memory']['total']
        self.allowed_vgs = []

        # If node bound to the cluster than it has a role
        # and volume groups which we should to allocate
        if node.cluster:
            volumes_metadata = node.cluster.release.volumes_metadata
            volume_groups_for_role = volumes_metadata[
                'volumes_roles_mapping'][node.role]

            # Adding volume groups in same order
            # as they represent in volumes_roles_mapping list
            for vg_name in volume_groups_for_role:
                vg = filter(lambda vg: vg.get('id') == vg_name,
                            volumes_metadata['volumes'])[0]
                self.allowed_vgs.append(vg)

        self.disks = []
        for d in sorted(node.meta['disks'], key=lambda i: i['name']):
            disks_count = len(node.meta["disks"])
            boot_is_raid = True if disks_count > 1 else False

            existing_disk = filter(
                lambda disk: d['disk'] == disk['id'],
                only_disks(self.volumes))

            disk_volumes = existing_disk[0].get('volumes', []) if existing_disk else []

            disk = Disk(
                disk_volumes,
                self.call_generator,
                d["disk"],
                d["name"],
                byte_to_megabyte(d["size"]),
                boot_is_raid=boot_is_raid,
                # Count of possible PVs equal to count of allowed VGs
                possible_pvs_count=len(self.allowed_vgs))

            self.disks.append(disk)

        self.__logger('Initialized with node: %s' % node.full_name)
        self.__logger('Initialized with volumes: %s' % json.dumps(self.volumes, indent=4))
        self.__logger('Initialized with disks: %s' % self.disks)

    def set_pv_size(self, disk_id, volume_name, size):
        self.__logger('Update PV size for disk=%s volume_name=%s size=%s' %
                      (disk_id, volume_name, size))

        disk = filter(lambda disk: disk.id == disk_id, self.disks)[0]
        disk.set_pv_size(volume_name, size)

        for idx, volume in enumerate(self.volumes):
            if volume.get('id') == disk.id:
                self.volumes[idx] = disk.render()

        # Recalculate sizes of volume groups
        for idx, volume in enumerate(self.volumes):
            if volume.get('type') == 'vg':
                vg_id = volume.get('id')
                vg_template = filter(
                    lambda volume: volume.get('id') == vg_id,
                    self.allowed_vgs)[0]

                self.volumes[idx] = self.expand_generators(vg_template)

        self.__logger('Updated volume size' % self.volumes)
        return self.volumes

    def get_pv_size(self, disk_id, volume_name):
        '''
        Get PV size without lvm meta
        '''
        disk = filter(
            lambda volume: volume['id'] == disk_id,
            only_disks(self.volumes))[0]

        volume = filter(
            lambda volume: volume_name == volume.get('vg'),
            disk['volumes'])[0]

        size_without_lvm_meta = volume['size'] - \
            self.call_generator('calc_lvm_meta_size')

        return size_without_lvm_meta

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
            'calc_min_glance_size': lambda: gb_to_mb(5),
            'calc_min_cinder_size': lambda: gb_to_mb(1.5),
            'calc_total_root_vg': self._calc_total_root_vg
        }

        generators['calc_os_size'] = \
            lambda: generators['calc_root_size']() + \
            generators['calc_swap_size']()

        generators['calc_os_vg_size'] = generators['calc_os_size']
        generators['calc_min_os_size'] = generators['calc_os_size']

        if not generator in generators:
            raise errors.CannotFindGenerator(
                u'Cannot find generator %s' % generator)

        result = generators[generator](*args)
        self.__logger('Generator %s with args %s returned result: %s' %
                      (generator, args, result))
        return result

    def _calc_total_root_vg(self):
        return self._calc_total_vg('os') - \
            self.call_generator('calc_swap_size')

    def _calc_total_vg(self, vg):
        vg_space = 0
        for v in only_disks(self.volumes):
            for subv in v['volumes']:
                if subv.get('type') == 'pv' and subv.get('vg') == vg:
                    vg_space += subv.get('size', 0) - \
                        subv.get('lvm_meta_size', 0)

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
        mem = float(self.ram) / 1024 ** 3
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
        self.__logger('Allocate volume group %s with size %s' % (name, size))

        if size is None:
            for disk in self.disks:
                if disk.free_space > 0:
                    self.__logger('Allocating all available space for PV: '
                                  'disk: %s vg: %s' % (disk.id, name))
                    disk.create_pv(name)
                else:
                    self.__logger('Not enough free space for PV allocation: '
                                  'disk: %s vg: %s' % (disk.id, name))
                    disk.create_pv(name, 0)
        else:
            not_allocated_size = size
            for disk in self.disks:
                self.__logger('Creating PV: disk: %s, vg: %s' %
                              (disk.id, name))

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
        self.__logger('Generating volumes info for node')
        self.__logger('Purging volumes info for all node disks')

        map(lambda d: d.reset(), self.disks)
        self.volumes = [d.render() for d in self.disks]

        if not self.allowed_vgs:
            self.__logger('Role is None return volumes: %s' % self.volumes)
            return self.volumes

        self.volumes.extend(self.allowed_vgs)

        for vg in self.allowed_vgs:
            # For last volume group in allowed_vgs list
            # we allocates all free space
            if len(self.allowed_vgs) == 1 or vg == self.allowed_vgs[-1]:
                self._allocate_vg(vg['id'])
            else:
                min_size = self.expand_generators(vg)['min_size']
                self._allocate_vg(vg['id'], min_size)

        self.volumes = self.expand_generators(self.volumes)
        self.__logger('Generated volumes: %s' % self.volumes)
        return self.volumes

    def expand_generators(self, cdict):
        new_dict = {}
        if isinstance(cdict, dict):
            for i, val in cdict.iteritems():
                if type(val) in (str, unicode, int, float):
                    new_dict[i] = val
                elif isinstance(val, dict):
                    if "generator" in val:
                        genval = self.call_generator(
                            val["generator"],
                            *(val.get("generator_args", []))
                        )
                        self.__logger(
                            'Generator %s with args %s expanded to: %s' %
                            (val['generator'],
                             val.get('generator_args', []),
                             genval))

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

        self.__logger('Checking disks space: disks space %s, minimal size %s' %
                      (disks_space, minimal_installation_size))

        if disks_space < minimal_installation_size:
            raise errors.NotEnoughFreeSpace()

    def __calc_minimal_installation_size(self):
        '''
        Calc minimal installation size depend on node role
        '''
        disks_count = len(filter(lambda disk: disk.size > 0, self.disks))
        boot_size = self.call_generator('calc_boot_size') + \
            self.call_generator('calc_boot_records_size')

        min_installation_size = disks_count * boot_size
        for vg in self.allowed_vgs:
            min_size = self.expand_generators(vg)['min_size']
            min_installation_size += min_size

        return min_installation_size

    def __logger(self, message):
        logger.debug('VolumeManager %s: %s', id(self), message)
