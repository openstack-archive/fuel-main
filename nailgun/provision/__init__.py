# -*- coding: utf-8 -*-

import re


class ProvisionException(Exception):
    pass


class ProvisionAlreadyExists(ProvisionException):
    pass


class ProvisionDoesNotExist(ProvisionException):
    pass


class ProvisionConfig:
    cn = 'nailgun.provision.driver.cobbler.Cobbler'


class Provision:
    def __init__(self):
        raise NotImplementedError(
            "Try to use ProvisionFactory.getInstance() method."
        )

    def save_profile(self):
        raise NotImplementedError

    def save_node(self):
        raise NotImplementedError


class ProvisionFactory:

    @classmethod
    def getInstance(cls, config=ProvisionConfig()):
        name = config.cn
        module_name = '.'.join(re.split(ur'\.', name)[:-1])
        class_name = re.split(ur'\.', name)[-1]
        return getattr(
            __import__(
                module_name,
                globals(),
                locals(),
                [class_name],
                -1
            ),
            class_name
        )(config)
