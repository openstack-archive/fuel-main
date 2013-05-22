# -*- coding: utf-8 -*-

from nailgun.logger import logger
from nailgun.errors.base import NailgunException


default_messages = {
    # deployment errors
    "DeploymentAlreadyStarted": "Deployment already started",
    "DeletionAlreadyStarted": "Environment removal already started",
    "FailedProvisioning": "Failed to start provisioning",
    "WrongNodeStatus": "Wrong node status",
    "NodeOffline": "Node is offline",
    # network errors
    "AdminNetworkNotFound": "Admin network info not found",
    "AssignIPError": "Failed to assign IP to node",
    "NetworkCheckError": "Network checking failed",
    "OutOfVLANs": "Not enough available VLAN IDs",
    "OutOfIPs": "Not enough free IP addresses in pool",
    "NoSuitableCIDR": "Cannot find suitable CIDR",
    # unknown
    "UnknownError": "Unknown error"
}


class ErrorFactory(object):

    def __init__(self):
        for name, msg in default_messages.iteritems():
            setattr(self, name, self._build_exc(name, msg))

    def _build_exc(self, name, msg):
        return type(
            name,
            (NailgunException,),
            {
                "message": msg
            }
        )

    def __getattr__(self, name):
        return self._build_exc(name, default_messages["UnknownError"])


errors = ErrorFactory()
