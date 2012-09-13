import logging
from provision import ProvisionException
from . import Validator


class Power:
    _power_user = None
    _power_pass = None
    _power_address = None
    _power_id = None

    def __init__(self, power_type):
        if Validator.is_powertype_valid(power_type):
            self._power_type = power_type
        else:
            raise ProvisionException("Power type is not valid")

    @property
    def power_type(self):
        return self._power_type

    @property
    def power_user(self):
        return self._power_user

    @power_user.setter
    def power_user(self, power_user):
        self._power_user = power_user

    @property
    def power_pass(self):
        return self._power_pass

    @power_pass.setter
    def power_pass(self, power_pass):
        self._power_pass = power_pass

    @property
    def power_address(self):
        return self._power_address

    @power_address.setter
    def power_address(self, power_address):
        self._power_address = power_address

    @property
    def power_id(self):
        return self._power_id

    @power_id.setter
    def power_id(self, power_id):
        self._power_id = power_id
