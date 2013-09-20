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

import web

from nailgun.api.handlers.cluster import ClusterAttributesDefaultsHandler
from nailgun.api.handlers.cluster import ClusterAttributesHandler
from nailgun.api.handlers.cluster import ClusterChangesHandler
from nailgun.api.handlers.cluster import ClusterCollectionHandler
from nailgun.api.handlers.cluster import ClusterGeneratedData
from nailgun.api.handlers.cluster import ClusterHandler
from nailgun.api.handlers.disks import NodeDefaultsDisksHandler
from nailgun.api.handlers.disks import NodeDisksHandler
from nailgun.api.handlers.disks import NodeVolumesInformationHandler

from nailgun.api.handlers.logs import LogEntryCollectionHandler
from nailgun.api.handlers.logs import LogPackageHandler
from nailgun.api.handlers.logs import LogSourceByNodeCollectionHandler
from nailgun.api.handlers.logs import LogSourceCollectionHandler

from nailgun.api.handlers.network_configuration \
    import NetworkConfigurationHandler
from nailgun.api.handlers.network_configuration \
    import NetworkConfigurationVerifyHandler

from nailgun.api.handlers.node import NodeCollectionHandler
from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.node import NodesAllocationStatsHandler

from nailgun.api.handlers.node import NodeCollectionNICsDefaultHandler
from nailgun.api.handlers.node import NodeCollectionNICsHandler
from nailgun.api.handlers.node import NodeNICsDefaultHandler
from nailgun.api.handlers.node import NodeNICsHandler
from nailgun.api.handlers.node import NodeNICsVerifyHandler

from nailgun.api.handlers.notifications import NotificationCollectionHandler
from nailgun.api.handlers.notifications import NotificationHandler

from nailgun.api.handlers.orchestrator import DefaultDeploymentInfo
from nailgun.api.handlers.orchestrator import DefaultProvisioningInfo
from nailgun.api.handlers.orchestrator import DeploymentInfo
from nailgun.api.handlers.orchestrator import ProvisioningInfo

from nailgun.api.handlers.plugin import PluginCollectionHandler
from nailgun.api.handlers.plugin import PluginHandler

from nailgun.api.handlers.redhat import RedHatAccountHandler
from nailgun.api.handlers.redhat import RedHatSetupHandler
from nailgun.api.handlers.registration import FuelKeyHandler
from nailgun.api.handlers.release import ReleaseCollectionHandler
from nailgun.api.handlers.release import ReleaseHandler

from nailgun.api.handlers.tasks import TaskCollectionHandler
from nailgun.api.handlers.tasks import TaskHandler

from nailgun.api.handlers.version import VersionHandler


urls = (
    r'/releases/?$',
    ReleaseCollectionHandler.__name__,
    r'/releases/(?P<release_id>\d+)/?$',
    ReleaseHandler.__name__,

    r'/clusters/?$',
    ClusterCollectionHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/?$',
    ClusterHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/changes/?$',
    ClusterChangesHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/attributes/?$',
    ClusterAttributesHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/attributes/defaults/?$',
    ClusterAttributesDefaultsHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/network_configuration/?$',
    NetworkConfigurationHandler.__name__,
    r'/clusters/(?P<cluster_id>\d+)/network_configuration/verify/?$',
    NetworkConfigurationVerifyHandler.__name__,

    r'/clusters/(?P<cluster_id>\d+)/orchestrator/deployment/?$',
    DeploymentInfo.__name__,
    r'/clusters/(?P<cluster_id>\d+)/orchestrator/deployment/defaults/?$',
    DefaultDeploymentInfo.__name__,
    r'/clusters/(?P<cluster_id>\d+)/orchestrator/provisioning/?$',
    ProvisioningInfo.__name__,
    r'/clusters/(?P<cluster_id>\d+)/orchestrator/provisioning/defaults/?$',
    DefaultProvisioningInfo.__name__,
    r'/clusters/(?P<cluster_id>\d+)/generated/?$',
    ClusterGeneratedData.__name__,

    r'/nodes/?$',
    NodeCollectionHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/?$',
    NodeHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/disks/?$',
    NodeDisksHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/disks/defaults/?$',
    NodeDefaultsDisksHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/volumes/?$',
    NodeVolumesInformationHandler.__name__,
    r'/nodes/interfaces/?$',
    NodeCollectionNICsHandler.__name__,
    r'/nodes/interfaces/default_assignment?$',
    NodeCollectionNICsDefaultHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/interfaces/?$',
    NodeNICsHandler.__name__,
    r'/nodes/(?P<node_id>\d+)/interfaces/default_assignment?$',
    NodeNICsDefaultHandler.__name__,
    r'/nodes/interfaces_verify/?$',
    NodeNICsVerifyHandler.__name__,
    r'/nodes/allocation/stats/?$',
    NodesAllocationStatsHandler.__name__,
    r'/tasks/?$',
    TaskCollectionHandler.__name__,
    r'/tasks/(?P<task_id>\d+)/?$',
    TaskHandler.__name__,

    r'/notifications/?$',
    NotificationCollectionHandler.__name__,
    r'/notifications/(?P<notification_id>\d+)/?$',
    NotificationHandler.__name__,

    r'/logs/?$',
    LogEntryCollectionHandler.__name__,
    r'/logs/package/?$',
    LogPackageHandler.__name__,
    r'/logs/sources/?$',
    LogSourceCollectionHandler.__name__,
    r'/logs/sources/nodes/(?P<node_id>\d+)/?$',
    LogSourceByNodeCollectionHandler.__name__,

    r'/registration/key/?$',
    FuelKeyHandler.__name__,

    r'/version/?$',
    VersionHandler.__name__,

    r'/plugins/?$',
    PluginCollectionHandler.__name__,
    r'/plugins/(?P<plugin_id>\d+)/?$',
    PluginHandler.__name__,
    r'/redhat/account/?$',
    RedHatAccountHandler.__name__,
    r'/redhat/setup/?$',
    RedHatSetupHandler.__name__,
)

app = web.application(urls, locals())
