# -*- coding: utf-8 -*-

import json

from nailgun.db import orm
from nailgun.logger import logger


class Disk(object):

    def __init__(self, vm, disk_id, size):
        self.vm = vm
        self.id = disk_id
        self.size = size
        self.free_space = size
        self.volumes = []

    def clear(self):
        self.volumes = []
        self.free_space = self.size

    def create_pv(self, vg, size=None):
        if size:
            size = size + self.vm.field_generator(
                "calc_lvm_meta_size"
            )
        elif size is None:
            size = self.free_space
        self.free_space = self.free_space - size

        for i, volume in enumerate(self.volumes):
            if (volume.get("type"), volume.get("vg")) == ("pv", vg):
                self.volumes[i]["size"] = size
                return

        self.volumes.append({
            "type": "pv",
            "vg": vg,
            "size": size
        })

    def create_partition(self, mount, size):
        self.volumes.append({
            "type": "partition",
            "mount": mount,
            "size": size
        })
        self.free_space = self.free_space - size

    def create_mbr(self, boot=False):
        if boot:
            self.volumes.append({"type": "mbr"})
        self.free_space = self.free_space - \
            self.vm.field_generator("calc_mbr_size")

    def make_bootable(self):
        self.create_partition(
            "/boot",
            self.vm.field_generator("calc_boot_size")
        )
        self.create_mbr(True)

    def render(self):
        return {
            "id": self.id,
            "type": "disk",
            "size": self.size,
            "volumes": self.volumes
        }

    def __repr__(self):
        return json.dumps(self.render(), indent=4)


class VolumeManager(object):

    def __init__(self, node):
        self.db = orm()
        self.node = node
        if not self.node:
            raise Exception(
                "Invalid node - can't generate volumes info"
            )
        self.volumes = []
        self.disks = []

    def _traverse(self, cdict):
        new_dict = {}
        if isinstance(cdict, dict):
            for i, val in cdict.iteritems():
                if type(val) in (str, unicode, int, float):
                    new_dict[i] = val
                elif isinstance(val, dict):
                    if "generator" in val:
                        new_dict[i] = self.field_generator(
                            val["generator"],
                            val.get("generator_args", [])
                        )
                    else:
                        new_dict[i] = self._traverse(val)
                elif isinstance(val, list):
                    new_dict[i] = []
                    for d in val:
                        new_dict[i].append(self._traverse(d))
        elif isinstance(cdict, list):
            new_dict = []
            for d in cdict:
                new_dict.append(self._traverse(d))
        return new_dict

    def field_generator(self, generator, args=None):
        if not args:
            args = []
        generators = {
            # swap = memory + 1Gb
            "calc_swap_size": lambda:
            self.node.meta["memory"]["total"] + 1024 ** 3,
            # root = 10Gb
            "calc_root_size": lambda: 1024 ** 3 * 10,
            "calc_boot_size": lambda: 1024 ** 2 * 200,
            # let's think that size of mbr is 1Mb
            "calc_mbr_size": lambda: 10 * 1024 ** 2,
            "calc_lvm_meta_size": lambda: 1024 ** 2 * 64
        }
        generators["calc_os_size"] = lambda: sum([
            generators["calc_root_size"](),
            generators["calc_swap_size"]()
        ])
        return generators.get(generator, lambda: None)(*args)

    def _allocate_vg(self, name, size=None, use_existing_space=True):
        free_space = sum([d.free_space for d in self.disks])

        if not size:
            for disk in self.disks:
                disk.create_pv(name, 0)
        if use_existing_space:
            for i, disk in enumerate(self.disks):
                if disk.free_space > 0:
                    disk.create_pv(name)

    def _allocate_os(self):
        os_size = self.field_generator("calc_os_size")
        boot_size = self.field_generator("calc_boot_size")
        mbr_size = self.field_generator("calc_mbr_size")
        lvm_meta_size = self.field_generator("calc_lvm_meta_size")

        free_space = sum([d.size - mbr_size for d in self.disks])

        if free_space < (os_size + boot_size):
            raise Exception("Insufficient disk space for OS")

        ready = False
        os_vg_size_left = os_size
        for i, disk in enumerate(self.disks):
            if i == 0:
                disk.make_bootable()
            else:
                disk.create_mbr()

            if os_vg_size_left == 0:
                disk.create_pv("os", 0)
                continue

            if disk.free_space > (
                os_vg_size_left + lvm_meta_size
            ):
                disk.create_pv("os", os_vg_size_left)
                os_vg_size_left = 0
            else:
                os_vg_size_left = os_vg_size_left - (
                    disk.free_space - lvm_meta_size
                )
                disk.create_pv("os")

    def gen_volumes_info(self):
        if not "disks" in self.node.meta:
            raise Exception("No disk metadata specified for node")
        logger.debug(
            u"Generating volumes info for node '{0}' (role:{1})".format(
                self.node.name or self.node.mac or self.node.id,
                self.node.role
            )
        )
        self.volumes = self.gen_default_volumes_info()
        if self.node.cluster:
            volumes_metadata = self.node.cluster.release.volumes_metadata
            map(lambda d: d.clear(), self.disks)
            self._allocate_os()
            self.volumes = [d.render() for d in self.disks]
            self.volumes.extend(
                volumes_metadata[self.node.role]
            )
            # UGLY HACK HERE
            # generate volume groups for node by role
            if self.node.role == "compute":
                self._allocate_vg("vm")
            elif self.node.role == "cinder":
                self._allocate_vg("cinder")
            self.volumes = self._traverse(self.volumes)
        return self.volumes

    def gen_default_volumes_info(self):
        if not "disks" in self.node.meta:
            raise Exception("No disk metadata specified for node")
        for disk in sorted(self.node.meta["disks"], key=lambda i: i["name"]):
            self.disks.append(Disk(self, disk["disk"], disk["size"]))

        self._allocate_os()
        self.volumes = [d.render() for d in self.disks]
        # creating volume groups
        self.volumes.extend([
            {
                "id": "os",
                "type": "vg",
                "volumes": [
                    {
                        "mount": "/",
                        "size": {"generator": "calc_root_size"},
                        "name": "root",
                        "type": "lv"
                    },
                    {
                        "mount": "swap",
                        "size": {"generator": "calc_swap_size"},
                        "name": "swap",
                        "type": "lv"
                    }
                ]
            },
            {
                "id": "vm",
                "type": "vg",
                "volumes": [
                    {"mount": "/var/lib/libvirt", "size": 0,
                     "name": "vm", "type": "lv"}
                ]
            }
        ])

        return self._traverse(self.volumes)
