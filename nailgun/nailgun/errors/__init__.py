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

from nailgun.logger import logger
from nailgun.errors.base import NailgunException


default_messages = {
    # common errors
    "InvalidData": "Invalid data received",
    "AlreadyExists": "Object already exists",

    # node discovering errors
    "InvalidInterfacesInfo": "Invalid interfaces info",
    "InvalidMetadata": "Invalid metadata specified for node",

    # deployment errors
    "DeploymentAlreadyStarted": "Deployment already started",
    "DeletionAlreadyStarted": "Environment removal already started",
    "FailedProvisioning": "Failed to start provisioning",
    "WrongNodeStatus": "Wrong node status",
    "NodeOffline": "Node is offline",
    "NotEnoughControllers": "Not enough controllers",

    # disk errors
    "NotEnoughFreeSpace": "Not enough free space",
    "CannotFindVolumesInfoForRole": "Cannot fund volumes info for role",

    # network errors
    "AdminNetworkNotFound": "Admin network info not found",
    "InvalidNetworkAccess": "Invalid network access",
    "AssignIPError": "Failed to assign IP to node",
    "NetworkCheckError": "Network checking failed",
    "OutOfVLANs": "Not enough available VLAN IDs",
    "OutOfIPs": "Not enough free IP addresses in pool",
    "NoSuitableCIDR": "Cannot find suitable CIDR",
    "CanNotFindInterface": "Cannot find interface",
    "CanNotDetermineEndPointIP": "Cannot determine end point IP",

    # plugin errors
    "PluginDownloading": "Cannot install plugin",
    "PluginInitialization": "Cannot initialize plugin",

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
