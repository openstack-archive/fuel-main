# -*- coding: utf-8 -*-

import json

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.errors import errors


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
        logger.debug("Creating or updating PV: disk=%s vg=%s, size=%s",
                     self.id, vg, str(size))
        # if required size in not equal to zero
        # we need to not forget to allocate lvm metadata space
        if size:
            size = size + self.vm.field_generator(
                "calc_lvm_meta_size"
            )
            logger.debug("Size + lvm_meta_size: %s", size)
        # if size is not defined we should
        # to allocate all available space
        elif size is None:
            logger.debug("Size is not defined. "
                         "Will use all free space on this disk.")
            size = self.free_space

        self.free_space = self.free_space - size
        logger.debug("Left free space: disk: %s free space: %s",
                     self.id, self.free_space)

        for i, volume in enumerate(self.volumes):
            if (volume.get("type"), volume.get("vg")) == ("pv", vg):
                logger.debug("PV already exist. Setting its size to: %s", size)
                self.volumes[i]["size"] = size
                return
        logger.debug("Appending PV to volumes.")
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
        logger.debug("Allocating MBR")
        self.free_space = self.free_space - \
            self.vm.field_generator("calc_mbr_size")

    def make_bootable(self):
        logger.debug("Allocating /boot partition")
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
        return json.dumps(self.render())

    def __str__(self):
        return json.dumps(self.render(), indent=4)


class VolumeManager(object):
    def __init__(self, node=None, data=None):
        """
        VolumeManager can be initialized with node
        and with data. Being initialized with node
        disks and volumes will be set according to node
        attributes. In later case disk and volumes will
        be set according to init data.
        """
        self.db = None
        self.node = None
        self.disks = []
        self.volumes = []
        if node:
            logger.debug("VolumeManager initialized with node: %s", node.id)
            self.db = orm()
            self.node = node
            self.volumes = self.node.attributes.volumes or []

            if not "disks" in self.node.meta:
                raise Exception("No disk metadata specified for node")
            for d in sorted(self.node.meta["disks"],
                            key=lambda i: i["name"]):
                disk = Disk(self, d["disk"], d["size"])
                for v in self.volumes:
                    if v.get("type") == "disk" and v.get("id") == disk.id:
                        disk.volumes = v.get("volumes", [])
                self.disks.append(disk)
        elif data:
            logger.debug("VolumeManager initialized with data: %s", data)
            for v in data:
                if v.get("type") == "disk" and v.get("id") and v.get("size"):
                    disk = Disk(self, v["id"], v["size"])
                    disk.volumes = v.get("volumes", [])
                    self.disks.append(disk)
                self.volumes.append(v)

        else:
            raise Exception("VolumeManager can't be initialized."
                            "Both node and data are None.")

        logger.debug("VolumeManager: volumes: %s", self.volumes)
        logger.debug("VolumeManager: disks: %s", self.disks)
        self.validate()

    def validate(self):
        logger.debug("Validating volumes")
        for i, vg in enumerate(self.volumes):
            if vg.get("type") == "vg" and vg.get("id") == "vm":
                for j, lv in enumerate(vg.get("volumes", [])):
                    if lv.get("type") == "lv" and lv.get("name") == "libvirt":
                        self.volumes[i]["volumes"][j]["size"] = \
                            self.field_generator("calc_total_vg", "vm")
            if vg.get("type") == "vg" and vg.get("id") == "os":
                for j, lv in enumerate(vg.get("volumes", [])):
                    if lv.get("type") == "lv" and lv.get("name") == "root":
                        self.volumes[i]["volumes"][j]["size"] += \
                            self.field_generator(
                                "calc_total_unallocated_vg", "os")
        return self.volumes

    def _traverse(self, cdict):
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
                        genval = self.field_generator(
                            val["generator"],
                            *(val.get("generator_args", []))
                        )
                        logger.debug("Generated value: %s", str(genval))
                        new_dict[i] = genval
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

    def _calc_root_size(self):
        role = self.node.role
        if role == 'controller':
            return 1024 ** 3 * 25
        else:
            return 1024 ** 3 * 10

    def _calc_os_vg_size(self):
        role = self.node.role
        if role == 'controller':
            return self.field_generator('calc_all_free') 
        else:
            return self.field_generator('calc_os_size')

    def _calc_swap_size(self):
        mem = float(self.node.meta["memory"]["total"]) / 1024 ** 3
        # See https://access.redhat.com/site/documentation/en-US/
        #             Red_Hat_Enterprise_Linux/6/html/Installation_Guide/
        #             s2-diskpartrecommend-ppc.html#id4394007
        if mem <= 2:
            return int(2 * mem * 1024 ** 3)
        elif mem > 2 and mem <= 8:
            return int(mem * 1024 ** 3)
        elif mem > 8 and mem <= 64:
            return int(.5 * mem * 1024 ** 3)
        else:
            return int(4 * 1024 ** 3)

    def _calc_all_free(self):
        logger.debug("_calc_all_free")
        return sum([d.free_space for d in self.disks])

    def _calc_total_vg(self, vg):
        logger.debug("_calc_total_vg")
        vg_space = 0
        for v in self.volumes:
            if v.get("type") == "disk" and v.get("volumes"):
                for subv in v["volumes"]:
                    if (subv.get("type"), subv.get("vg")) == ("pv", vg):
                        vg_space += (subv.get("size", 0) -
                                     self.field_generator(
                                         "calc_lvm_meta_size"))
        return vg_space

    def _calc_total_unallocated_vg(self, vg):
        logger.debug("_calc_total_unallocated_vg")
        vg_space = self._calc_total_vg(vg)
        for v in self.volumes:
            if v.get("type") == "vg" and v.get("id") == vg:
                for subv in v.get("volumes", []):
                    vg_space -= subv.get("size", 0)
        return vg_space

    def field_generator(self, generator, *args):
        generators = {
            # Calculate swap space based on total RAM
            "calc_swap_size": self._calc_swap_size,
            # root = 10Gb
            "calc_root_size": self._calc_root_size,
            "calc_boot_size": lambda: 1024 ** 2 * 200,
            # let's think that size of mbr is 10Mb
            "calc_mbr_size": lambda: 10 * 1024 ** 2,
            "calc_lvm_meta_size": lambda: 1024 ** 2 * 64,
            "calc_all_free": self._calc_all_free,
            "calc_os_vg_size": self._calc_os_vg_size,
            "calc_total_vg": self._calc_total_vg,
            "calc_total_unallocated_vg": self._calc_total_unallocated_vg,
        }
        generators["calc_os_size"] = lambda: sum([
            generators["calc_root_size"](),
            generators["calc_swap_size"]()
        ])
        return generators.get(generator, lambda: None)(*args)

    def _allocate_vg(self, name, size=None, use_existing_space=True):
        logger.debug("_allocate_vg: vg: %s, size: %s", name, str(size))
        free_space = sum([d.free_space for d in self.disks])
        logger.debug("Available free space on all disks: %s", str(free_space))

        # Is size is not defined or zero we just add
        # zero size PVs on all disks. We just need to have
        # all volume groups PVs on all disks despite their size.
        # Zero size PVs are needed
        # for UI to display disks correctly. When zero size
        # PV is passed to cobbler ks_meta, partition snippet will
        # ignore it.
        if not size:
            for disk in self.disks:
                logger.debug("Creating zero size PV: disk: %s, vg: %s",
                             disk.id, name)
                disk.create_pv(name, 0)
        # If we want to allocate all available size for volume group
        # we need to call create_pv method without setting
        # explicit size and we need to do this for every disk.
        # Keep in mind that when you call create_pv(name, size)
        # this method will actually try to create PV with size + lvm_meta_size
        if use_existing_space:
            for i, disk in enumerate(self.disks):
                if disk.free_space > 0:
                    logger.debug("Allocating all available space for PV: "
                                 "disk: %s vg: %s", disk.id, name)
                    disk.create_pv(name)

    def _allocate_os(self):
        logger.debug("_allocate_os")
        os_vg_size_left = self.field_generator("calc_os_vg_size")
        lvm_meta_size = self.field_generator("calc_lvm_meta_size")

        ready = False
        logger.debug("Iterating over node disks.")
        for i, disk in enumerate(self.disks):
            logger.debug("Found disk: %s", disk.id)
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
        if not self.node:
            raise Exception("Node is not defined")

        logger.debug(
            u"Generating volumes info for node '{0}' (role:{1})".format(
                self.node.name or self.node.mac or self.node.id,
                self.node.role
            )
        )

        logger.debug("Purging volumes info for all node disks")
        map(lambda d: d.clear(), self.disks)

        if not self.node.cluster:
            logger.debug("Node is not bound to cluster.")
            return self.gen_default_volumes_info()
        else:
            volumes_metadata = self.node.cluster.release.volumes_metadata

            self._allocate_os()
            self.volumes = [d.render() for d in self.disks]
            self.volumes.extend(
                volumes_metadata[self.node.role]
            )
            # UGLY HACK HERE
            # generate volume groups for node by role
            if self.node.role == "compute":
                logger.debug("Node role is compute. "
                             "Allocating volume group 'vm'")
                self._allocate_vg("vm")

            elif self.node.role == "cinder":
                logger.debug("Node role is cinder. "
                             "Allocating volume group 'cinder'")
                self._allocate_vg("cinder")

        logger.debug("Generating values for volumes")
        return self._traverse(self.volumes)

    def gen_default_volumes_info(self):
        logger.debug("Generating default volumes info")

        logger.debug("Purging volumes info for all disks")
        map(lambda d: d.clear(), self.disks)

        self._allocate_os()
        self.volumes = [d.render() for d in self.disks]
        logger.debug("Appending default OS volume group")
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
            }
        ])
        logger.debug("Generating values for volumes")
        return self._traverse(self.volumes)

    def check_free_space(self):
        """
        Check disks free space for OS installation

        :raises: errors.NotEnoughFreeSpace
        """
        os_size = self.field_generator("calc_os_size")
        boot_size = self.field_generator("calc_boot_size")
        mbr_size = self.field_generator("calc_mbr_size")
        free_space = sum([d.size - mbr_size for d in self.disks])

        if free_space < (os_size + boot_size):
            raise errors.NotEnoughFreeSpace(
                "Node '%s' has insufficient disk space for OS" %
                self.node.human_readable_name)
