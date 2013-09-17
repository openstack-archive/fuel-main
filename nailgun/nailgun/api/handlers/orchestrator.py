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

from nailgun.api.handlers.base import content_json
from nailgun.api.handlers.base import JSONHandler
from nailgun.api.models import Cluster
from nailgun.db import db
from nailgun.logger import logger
from nailgun.orchestrator import deployment_serializers
from nailgun.orchestrator import provisioning_serializers


class DefaultOrchestratorInfo(JSONHandler):
    """Base class for default orchestrator data."""

    def serialize(self, cluster):
        """Method should serialize cluster"""
        raise NotImplementedError('Please Implement this method')

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized default data which will be passed to orchestrator
        :http: * 200 (OK)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)
        return self.serialize(cluster)


class OrchestratorInfo(JSONHandler):
    """Base class for replaced data."""

    def get_orchestrator_info(self, cluster):
        """Method should return data
        which will be passed to orchestrator
        """
        raise NotImplementedError('Please Implement this method')

    def update_orchestrator_info(self, cluster, data):
        """Method should override data which
        will be passed to orchestrator
        """
        raise NotImplementedError('Please Implement this method')

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized data which will be passed to orchestrator
        :http: * 200 (OK)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)
        return self.get_orchestrator_info(cluster)

    @content_json
    def PUT(self, cluster_id):
        """:returns: JSONized data which will be passed to orchestrator
        :http: * 200 (OK)
               * 400 (wrong data specified)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)
        data = self.checked_data()
        self.update_orchestrator_info(cluster, data)
        logger.debug('OrchestratorInfo:'
                     ' facts for cluster_id {0} were uploaded'
                     .format(cluster_id))
        return data

    @content_json
    def DELETE(self, cluster_id):
        """:returns: {}
        :http: * 202 (orchestrator data deletion process launched)
               * 400 (failed to execute orchestrator data deletion process)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)
        self.update_orchestrator_info(cluster, {})
        raise web.accepted(data="{}")


class DefaultProvisioningInfo(DefaultOrchestratorInfo):

    def serialize(self, cluster):
        return provisioning_serializers.serialize(cluster)


class DefaultDeploymentInfo(DefaultOrchestratorInfo):

    def serialize(self, cluster):
        return deployment_serializers.serialize(cluster)


class ProvisioningInfo(OrchestratorInfo):

    def get_orchestrator_info(self, cluster):
        return cluster.replaced_provisioning_info

    def update_orchestrator_info(self, cluster, data):
        cluster.replaced_provisioning_info = data
        db().commit()
        return cluster.replaced_provisioning_info


class DeploymentInfo(OrchestratorInfo):

    def get_orchestrator_info(self, cluster):
        return cluster.replaced_deployment_info

    def update_orchestrator_info(self, cluster, data):
        cluster.replaced_deployment_info = data
        db().commit()
        return cluster.replaced_deployment_info
