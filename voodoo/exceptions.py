from jpic.exceptions import JpicException

class VoodooException(JpicException):
    pass

class PropertyInitialiserMissing(VoodooException):
    def __init__(self, raiser, name):
        msg = "Prop. %s missing from object %s of class %s (%s)" % (name, unicode(raiser), raiser.__class__.__name__, raiser.__class__ )
        super(PropertyInitialiserMissing, self).__init__(msg)
