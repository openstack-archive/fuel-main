# TODO(enchantner): create exceptions for handling different situations


class EmptyListError(LookupError):
    pass


class SSHError(Exception):
    pass


class DeployError(Exception):
    pass
