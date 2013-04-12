# -*- coding: utf-8 -*-

from nailgun.db import orm
from nailgun.logger import logger


class VolumeManager(object):

    def __init__(self, node):
        self.db = orm()
        self.node = node
        if not self.node:
            raise Exception(
                "Invalid node - can't generate volumes info"
            )
        self.volumes = []

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
            # let's think that size of mbr is 2Mb (more than usual, for safety)
            "calc_mbr_size": lambda: 1024 ** 2 * 2,
        }
        generators["calc_os_size"] = lambda: sum([
            generators["calc_root_size"](),
            generators["calc_swap_size"]()
        ])
        return generators.get(generator, lambda: None)(*args)

    def gen_volumes_info(self):
        if not "disks" in self.node.meta:
            raise Exception("No disk metadata specified for node")
        logger.debug(
            "Generating volumes info for node '{0}' (role:{1})".format(
                self.node.name or self.node.mac or self.node.id,
                self.node.role
            )
        )
        self.volumes = self.gen_default_volumes_info()
        if not self.node.cluster:
            return self.volumes
        volumes_metadata = self.node.cluster.release.volumes_metadata
        self.volumes = filter(
            lambda a: a["type"] == "disk",
            default_volumes
        )
        self.volumes.extend(
            volumes_metadata[self.node.role]
        )
        self.volumes = self._traverse(self.volumes)
        return self.volumes

    def gen_default_volumes_info(self):
        if not "disks" in self.node.meta:
            raise Exception("No disk metadata specified for node")
        for disk in self.node.meta["disks"]:
            self.volumes.append(
                {
                    "id": disk["disk"],
                    "type": "disk",
                    "size": disk["size"],
                    "volumes": [
                        {"type": "pv", "vg": "os", "size": 0},
                        {"type": "pv", "vg": "vm", "size": 0},
                        {"type": "pv", "vg": "cinder", "size": 0}
                    ]
                }
            )

        # minimal space for OS + boot
        os_size = sum([
            self.field_generator("calc_os_size"),
            self.field_generator("calc_boot_size"),
            self.field_generator("calc_mbr_size")
        ])

        disk_size = sum([
            disk["size"] for disk in self.node.meta["disks"]
        ])

        if disk_size < os_size:
            raise Exception("Insufficient disk space for OS")

        def create_boot_sector(v):
            v["volumes"].append(
                {
                    "type": "partition",
                    "mount": "/boot",
                    "size": {"generator": "calc_boot_size"}
                }
            )
            # let's think that size of mbr is 2Mb (more than usual, for safety)
            v["volumes"].append(
                {"type": "mbr"}
            )

        os_space = os_size
        for i, vol in enumerate(self.volumes):
            if vol["type"] != "disk":
                continue
            if i == 0 and vol["size"] > os_space:
                # all OS and boot on first disk
                vol["volumes"][0]["size"] = os_space - (
                    self.field_generator("calc_boot_size") +
                    self.field_generator("calc_mbr_size")
                )
                create_boot_sector(vol)
                break
            elif i == 0:
                # first disk: boot + part of OS
                vol["volumes"][0]["size"] = vol["size"] - (
                    self.field_generator("calc_boot_size") +
                    self.field_generator("calc_mbr_size")
                )
                create_boot_sector(vol)
                os_space = os_space - (
                    vol["volumes"][0]["size"] +
                    self.field_generator("calc_boot_size") +
                    self.field_generator("calc_mbr_size")
                )
            elif vol["size"] > os_space:
                # another disk: remaining OS
                vol["volumes"][0]["size"] = os_space
                break
            else:
                # another disk: part of OS
                vol["volumes"][0]["size"] = vol["size"]
                os_space = os_space - vol["volumes"][0]["size"]

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
