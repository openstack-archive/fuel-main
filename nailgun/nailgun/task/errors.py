# -*- coding: utf-8 -*-


class DeploymentAlreadyStarted(Exception):
    def __init__(
        self,
        message="Deployment already started"
    ):
        super(DeploymentAlreadyStarted, self).__init__(message)


class DeletionAlreadyStarted(Exception):
    def __init__(
        self,
        message="Cluster deletion already started"
    ):
        super(DeletionAlreadyStarted, self).__init__(message)


class FailedProvisioning(Exception):
    def __init__(
        self,
        message="Failed to start provisioning"
    ):
        super(FailedProvisioning, self).__init__(message)


class WrongNodeStatus(Exception):
    def __init__(
        self,
        message="Wrong node status"
    ):
        super(WrongNodeStatus, self).__init__(message)
