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

import json
import unittest
from copy import deepcopy

from nailgun.errors import errors
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.volumes.manager import Disk
from nailgun.volumes.manager import DisksFormatConvertor
from nailgun.volumes.manager import only_disks
from nailgun.volumes.manager import only_vg


class TestNodeDisksHandlers(BaseHandlers):

    def create_node(self, role='controller'):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[{
                'role': role,
                'pending_addition': True,
                'api': True}])

        return self.env.nodes[0]

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeDisksHandler', kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def put(self, node_id, data, expect_errors=False):
        resp = self.app.put(
            reverse('NodeDisksHandler', kwargs={'node_id': node_id}),
            json.dumps(data),
            headers=self.default_headers,
            expect_errors=expect_errors)

        if not expect_errors:
            self.assertEquals(200, resp.status)
            return json.loads(resp.body)
        else:
            return resp

    def test_default_attrs_after_creation(self):
        self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        disks = self.get(node_db.id)

        self.assertGreater(len(disks), 0)
        for disk in disks:
            self.assertTrue(type(disk['size']) == int)
            self.assertGreaterEqual(disk['size'], 0)
            self.assertEqual(len(disk['volumes']), 0)

    def test_disks_recreation_after_node_agent_request(self):
        self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        response = self.put(node_db.id, [])
        self.assertEquals(response, [])

        response = self.get(node_db.id)
        self.assertEquals(response, [])

        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{"mac": node_db.mac, "is_agent": True}]),
            headers=self.default_headers)
        self.assertEquals(200, resp.status)

        response = self.get(node_db.id)
        self.assertNotEquals(response, [])

    def test_disks_volumes_size_update(self):
        node_db = self.create_node()
        disks = self.get(node_db.id)
        for disk in disks:
            if disk['size'] > 0:
                for volume in disk['volumes']:
                    volume['size'] = 4200
        expect_disks = deepcopy(disks)

        response = self.put(node_db.id, disks)
        self.assertEquals(response, expect_disks)

        response = self.get(node_db.id)
        self.assertEquals(response, expect_disks)

    def test_recalculates_vg_sizes_when_disks_volumes_size_update(self):
        node_db = self.create_node()
        disks = self.get(node_db.id)

        vgs_before_update = filter(
            lambda volume: volume.get('type') == 'vg',
            node_db.attributes.volumes)

        new_volume_size = 4200
        updated_disks_count = 0
        for disk in disks:
            if disk['size'] > 0:
                for volume in disk['volumes']:
                    volume['size'] = new_volume_size
                updated_disks_count += 1

        self.put(node_db.id, disks)

        vgs_after_update = filter(
            lambda volume: volume.get('type') == 'vg',
            node_db.attributes.volumes)

        for vg_before, vg_after in zip(vgs_before_update, vgs_after_update):
            size_volumes_before = sum([
                volume.get('size', 0) for volume in vg_before['volumes']])
            size_volumes_after = sum([
                volume.get('size', 0) for volume in vg_after['volumes']])

            self.assertNotEquals(size_volumes_before, size_volumes_after)

            volume_group_size = new_volume_size * updated_disks_count
            self.assertEquals(size_volumes_after, volume_group_size)

    def test_validator_not_enough_size_for_volumes(self):
        node = self.create_node()
        disks = self.get(node.id)

        for disk in disks:
            if disk['size'] > 0:
                for volume in disk['volumes']:
                    volume['size'] = disk['size'] + 1

        response = self.put(node.id, disks, True)
        self.assertEquals(response.status, 400)
        self.assertRegexpMatches(
            response.body, '^Not enough free space on disk: .+')

    def test_validator_invalid_data(self):
        node = self.create_node()
        disks = self.get(node.id)

        for disk in disks:
            for volume in disk['volumes']:
                del volume['size']

        response = self.put(node.id, disks, True)
        self.assertEquals(response.status, 400)
        self.assertRegexpMatches(
            response.body, "'size' is a required property")


class TestNodeDefaultsDisksHandler(BaseHandlers):

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeDefaultsDisksHandler', kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def test_node_disk_amount_regenerates_volumes_info_if_new_disk_added(self):
        cluster = self.env.create_cluster(api=False)
        self.env.create_node(
            api=True,
            role='compute',  # vgs: os, vm
            cluster_id=cluster.id)
        node_db = self.env.nodes[0]
        response = self.get(node_db.id)
        self.assertEquals(len(response), 6)

        new_meta = node_db.meta.copy()
        new_meta['disks'].append({
            'size': 1000022933376,
            'model': 'SAMSUNG B00B135',
            'name': 'sda',
            'disk': 'disk/id/b00b135'})

        self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{
                "mac": node_db.mac,
                "meta": new_meta,
                "is_agent": True}]),
            headers=self.default_headers)

        self.env.refresh_nodes()

        response = self.get(node_db.id)
        self.assertEquals(len(response), 7)

        # check all groups on all disks
        vgs = ['os', 'vm']
        for disk in response:
            self.assertEquals(len(disk['volumes']), len(vgs))

    def test_get_default_attrs(self):
        self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        volumes_from_api = self.get(node_db.id)

        default_volumes = node_db.volume_manager.gen_volumes_info()
        disks = only_disks(default_volumes)

        self.assertEquals(len(disks), len(volumes_from_api))


class TestNodeVolumesInformationHandler(BaseHandlers):

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeVolumesInformationHandler',
                    kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def create_node(self, role):
        self.env.create(
            nodes_kwargs=[{'roles': [role], 'pending_addition': True}])

        return self.env.nodes[0]

    def check_volumes(self, volumes, volumes_ids):
        self.assertEquals(len(volumes), len(volumes_ids))
        for volume_id in volumes_ids:
            # Volume has name
            volume = filter(
                lambda volume: volume['name'] == volume_id, volumes)[0]
            # min_size
            self.assertTrue(type(volume['min_size']) == int)
            self.assertGreaterEqual(volume['min_size'], 0)
            # and label
            self.assertTrue(type(volume['label']) in (str, unicode))
            self.assertGreater(volume['label'], 0)

    def test_volumes_information_for_cinder_role(self):
        node_db = self.create_node('cinder')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os', 'cinder'])

    def test_volumes_information_for_compute_role(self):
        node_db = self.create_node('compute')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os', 'vm'])

    def test_volumes_information_for_controller_role(self):
        node_db = self.create_node('controller')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os', 'image'])


class TestVolumeManager(BaseHandlers):

    def create_node(self, role):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[{
                'roles': [role],
                'pending_addition': True,
                'api': True}])

        return self.env.nodes[-1]

    def non_zero_size(self, size):
        self.assertTrue(type(size) == int)
        self.assertGreater(size, 0)

    def os_size(self, disks, with_lvm_meta=True):
        os_sum_size = 0
        for disk in only_disks(disks):
            os_volume = filter(
                lambda volume: volume.get('vg') == 'os', disk['volumes'])[0]

            os_sum_size += os_volume['size']
            if not with_lvm_meta:
                os_sum_size -= os_volume['lvm_meta_size']

        self.non_zero_size(os_sum_size)
        return os_sum_size

    def glance_size(self, disks):
        glance_sum_size = 0
        for disk in only_disks(disks):
            glance_volume = filter(
                lambda volume: volume.get('vg') == 'image', disk['volumes']
            )[0]
            glance_sum_size += glance_volume['size']

        self.non_zero_size(glance_sum_size)
        return glance_sum_size

    def reserved_size(self, spaces):
        reserved_size = 0
        for disk in only_disks(spaces):
            reserved_size += DisksFormatConvertor.\
                calculate_service_partitions_size(disk['volumes'])

        return reserved_size

    def should_contain_os_with_minimal_size(self, volume_manager):
        self.assertEquals(
            self.os_size(volume_manager.volumes, with_lvm_meta=False),
            volume_manager.call_generator('calc_min_os_size'))

    def all_free_space_except_os_for_volume(self, spaces, volume_name):
        os_size = self.os_size(spaces)
        reserved_size = self.reserved_size(spaces)
        disk_sum_size = sum([disk['size'] for disk in only_disks(spaces)])
        vg_size = 0
        sum_lvm_meta = 0
        for disk in only_disks(spaces):
            for volume in disk['volumes']:
                if volume.get('vg') == volume_name:
                    vg_size += volume['size']
                    vg_size -= volume['lvm_meta_size']
                    sum_lvm_meta += volume['lvm_meta_size']

        self.assertEquals(
            vg_size, disk_sum_size - os_size - reserved_size - sum_lvm_meta)

    def logical_volume_sizes_should_equal_all_phisical_volumes(self, spaces):
        vg_sizes = {}
        for vg in only_vg(spaces):
            for volume in vg['volumes']:
                vg_name = vg['id']
                if not vg_sizes.get(vg_name):
                    vg_sizes[vg_name] = 0
                vg_sizes[vg_name] += volume['size']

        pv_sizes = {}
        for disk in only_disks(spaces):
            for volume in disk['volumes']:
                if volume['type'] == 'pv':
                    vg_name = volume['vg']
                    if not pv_sizes.get(vg_name):
                        pv_sizes[vg_name] = 0

                    pv_sizes[vg_name] += volume['size']
                    pv_sizes[vg_name] -= volume['lvm_meta_size']

        self.assertEquals(vg_sizes, pv_sizes)

    def check_disk_size_equal_sum_of_all_volumes(self, spaces):
        for disk in only_disks(spaces):
            volumes_size = sum(
                [volume.get('size', 0) for volume in disk['volumes']])

            self.assertEquals(volumes_size, disk['size'])

    def test_allocates_all_free_space_for_os_for_controller_role(self):
        node = self.create_node('controller')
        disks = only_disks(node.volume_manager.volumes)
        disks_size_sum = sum([disk['size'] for disk in disks])
        os_sum_size = self.os_size(disks)
        glance_sum_size = self.glance_size(disks)
        reserved_size = self.reserved_size(disks)

        self.assertEquals(disks_size_sum - reserved_size,
                          os_sum_size + glance_sum_size)
        self.logical_volume_sizes_should_equal_all_phisical_volumes(
            node.attributes.volumes)
        self.check_disk_size_equal_sum_of_all_volumes(node.attributes.volumes)

    def test_allocates_all_free_space_for_vm_for_compute_role(self):
        node = self.create_node('compute')
        self.should_contain_os_with_minimal_size(node.volume_manager)
        self.all_free_space_except_os_for_volume(
            node.volume_manager.volumes, 'vm')
        self.logical_volume_sizes_should_equal_all_phisical_volumes(
            node.attributes.volumes)
        self.check_disk_size_equal_sum_of_all_volumes(node.attributes.volumes)

    def test_allocates_all_free_space_for_vm_for_cinder_role(self):
        node = self.create_node('cinder')
        self.should_contain_os_with_minimal_size(node.volume_manager)
        self.all_free_space_except_os_for_volume(
            node.volume_manager.volumes, 'cinder')
        self.check_disk_size_equal_sum_of_all_volumes(node.attributes.volumes)

    def create_node_and_calculate_min_size(
            self, role, vg_names, volumes_metadata):
        node = self.create_node(role)
        volume_manager = node.volume_manager
        volumes = volume_manager.expand_generators(
            volumes_metadata['volumes'])

        min_installation_size = sum([
            volume['min_size'] for volume in
            filter(lambda volume: volume['id'] in vg_names, volumes)])

        boot_data_size = volume_manager.call_generator('calc_boot_size') +\
            volume_manager.call_generator('calc_boot_records_size')

        min_installation_size += boot_data_size

        return node, min_installation_size

    def update_node_with_single_disk(self, node, size):
        new_meta = node.meta.copy()
        new_meta['disks'] = [{
            # convert mbytes to bytes
            'size': size * (1024 ** 2),
            'model': 'SAMSUNG B00B135',
            'name': 'sda',
            'disk': 'disk/id/b00b135'}]

        self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{
                'mac': node.mac,
                'meta': new_meta,
                'is_agent': True}]),
            headers=self.default_headers)

    def test_check_disk_space_for_deployment(self):
        volumes_metadata = self.env.get_default_volumes_metadata()
        volumes_roles_mapping = volumes_metadata['volumes_roles_mapping']

        for role, vg_names in volumes_roles_mapping.iteritems():
            node, min_installation_size = self.\
                create_node_and_calculate_min_size(
                    role, vg_names, volumes_metadata)

            self.update_node_with_single_disk(node, min_installation_size)
            node.volume_manager.check_disk_space_for_deployment()

            self.update_node_with_single_disk(node, min_installation_size - 1)
            self.assertRaises(
                errors.NotEnoughFreeSpace,
                node.volume_manager.check_disk_space_for_deployment)


class TestDisks(BaseHandlers):

    def get_boot(self, volumes):
        return filter(
            lambda volume: volume.get('mount') == '/boot',
            volumes)[0]

    def create_disk(self, boot_is_raid=False, possible_pvs_count=0):
        return Disk(
            [], lambda name: 100, 'sda', 'sda', 10000,
            boot_is_raid=boot_is_raid, possible_pvs_count=possible_pvs_count)

    def test_create_mbr_as_raid_if_disks_count_greater_than_zero(self):
        disk = self.create_disk(boot_is_raid=True)
        boot_partition = self.get_boot(disk.volumes)
        self.assertEquals(boot_partition['type'], 'raid')

    def test_create_mbr_as_partition_if_disks_count_less_than_zero(self):
        disk = self.create_disk()
        boot_partition = self.get_boot(disk.volumes)
        self.assertEquals(boot_partition['type'], 'partition')

    def test_remove_pv(self):
        disk = self.create_disk(possible_pvs_count=1)
        disk_without_pv = deepcopy(disk)
        disk.create_pv('pv_name', 100)
        disk.remove_pv('pv_name')

        self.assertEquals(disk_without_pv.render(), disk.render())
