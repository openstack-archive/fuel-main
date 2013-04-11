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

    def field_generator(self, generator, args):
        generators = {
            # swap = memory + 1Gb
            "calc_swap_size": lambda:
            self.node.meta["memory"]["total"] + 1024 ** 3,
            # root = 10Gb
            "calc_root_size": lambda: 1024 ** 3 * 10
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
        default_volumes = self.gen_default_volumes_info()
        if not self.node.cluster:
            return default_volumes
        volumes_metadata = self.node.cluster.release.volumes_metadata
        volumes = filter(
            lambda a: a["type"] == "disk",
            default_volumes
        )
        volumes.extend(
            volumes_metadata[self.node.role]
        )
        volumes = self._traverse(volumes)
        return volumes

    def gen_default_volumes_info(self):
        if not "disks" in self.node.meta:
            raise Exception("No disk metadata specified for node")
        volumes = []
        for disk in self.node.meta["disks"]:
            volumes.append(
                {
                    "id": disk["disk"],
                    "type": "disk",
                    "volumes": [
                        {"type": "pv", "vg": "os", "size": 0},
                        {"type": "pv", "vg": "vm", "size": 0},
                        {"type": "pv", "vg": "cinder", "size": 0}
                    ]
                }
            )

        # auto assigning all stuff to first disk
        volumes[0]["volumes"][0]["size"] = {
            "generator": "calc_os_size"
        }
        volumes[0]["volumes"].append(
            {"type": "partition", "mount": "/boot", "size": 200 * 1024 ** 2}
        )
        volumes[0]["volumes"].append(
            {"type": "mbr"}
        )

        # creating volume groups
        volumes.extend([
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
                "id": "vms",
                "type": "vg",
                "volumes": [
                    {"mount": "/var/lib/libvirt", "size": 0,
                     "name": "vm", "type": "lv"}
                ]
            }
        ])

        return self._traverse(volumes)
