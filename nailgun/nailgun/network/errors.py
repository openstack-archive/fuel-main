# -*- coding: utf-8 -*-


class OutOfVLANs(Exception):

    def __init__(self, message, *args, **kwargs):
        if not message:
            message = u"Not enough available VLAN IDs"
        super(OutOfVLANs, self).__init__(message, *args, **kwargs)


class OutOfIPs(Exception):

    def __init__(self, message, *args, **kwargs):
        if not message:
            message = u"Not enough free IP addresses in pool"
        super(OutOfIPs, self).__init__(message, *args, **kwargs)


class NoSuitableCIDR(Exception):

    def __init__(self, message, *args, **kwargs):
        if not message:
            message = u"Cannot find suitable CIDR"
        super(NoSuitableCIDR, self).__init__(message, *args, **kwargs)


class CanNotFindInterface(Exception):

    def __init__(self, message, *args, **kwargs):
        if not message:
            message = u"Cannot find interface"
        super(
            CanNotFindAdminNetworkInterface,
            self).__init__(message, *args, **kwargs)
