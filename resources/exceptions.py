from jpic.exceptions import JpicException

class ResourceException(JpicException):
    pass

class AlreadyRegistered(ResourceException):
    pass

class NotRegistered(ResourceException):
    pass

class NotAsInline(ResourceException):
    pass

class UnnamedResourceException(ResourceException):
    def __init__(self, kwargs):
        msg = "Need either name or urlname in either: class attributes, Resource constructor arguments or Resource instance"
        super(UnnamedResourceException, self).__init__(msg)
