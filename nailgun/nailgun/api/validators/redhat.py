from nailgun.api.validators.base import BasicValidator
from nailgun.errors import errors


class RedHatAcountValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if not "license_type" in d:
            raise errors.InvalidData(
                message="No License Type specified"
            )
        if d["license_type"] not in ["rhsm", "rhn"]:
            raise errors.InvalidData(
                message="Invalid License Type"
            )
        if d["license_type"] == "rhsm":
            if "username" not in d or "password" not in d:
                raise errors.InvalidData(
                    message="Username or password not specified"
                )
        else:
            if "hostname" not in d or "activation_key" not in d:
                raise errors.InvalidData(
                    message="Satellite hostname or activation key "
                            "not specified"
                )
        if settings.FAKE_TASKS:
            pass
        else:
            # TODO: check Red Hat Account credentials
            pass
