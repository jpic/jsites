PROFILE=('pri', 'loop', 'method')
#PROFILE=()
TEST=True
PROFILE_INDENT='    '

class PropertyInitialiserMissing(Exception):
    def __init__(self, raiser, name):
        msg = "Prop. %s missing from object %s of class %s (%s)" % (name, unicode(raiser), raiser.__class__.__name__, raiser.__class__ )
        super(PropertyInitialiserMissing, self).__init__(msg)

class ProgrammablePropertyInitialiser(object):
    _indent=-1
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)
    def __getattr__(self, name):
        # pass out if its not something we want to touch
        if name[:1] == '_':
            return super(ProgrammablePropertyInitialiser, self).__getattribute__(name)
        self._indent+=1
        if 'pri' in PROFILE:
            print "%s- Programmable variable requested: %s" % (self._indent*PROFILE_INDENT, name)

        # check if the requested getter is avalaible
        if self.is_getter(name):
            try:
                return super(ProgrammablePropertyInitialiser, self).__getattribute__(name)
            except AttributeError:
                raise PropertyInitialiserMissing(self, name)

        stack = []
        value = None
        # first check in the instance class itself
        cls = self.__class__
        # search for the first descending parent
        # for the getter or class variable
        while self._getter(name) not in cls.__dict__ \
            and not name in cls.__dict__:
                if not stack or item > len(stack)-1:
                    # fill the empty stack
                    # maybe this won't work with multiple inheritance
                    # make a tiein if you need multiple inheritance FFS
                    stack = cls.__bases__
                    if not stack:
                        raise PropertyInitialiserMissing(self, name)
                    item = 0
                    if 'stack' in PROFILE:
                        print "%sNew stack of classes to check %s" % (
                            self._indent*PROFILE_INDENT, unicode(stack))
                # get next parent
                cls = stack[item]
                item+= 1
                if 'loop' in PROFILE:
                    print "%sChecking for %s (#%s) or %s() in %s" % (
                        self._indent*PROFILE_INDENT, name, item,  self._getter(name), cls)
        
        # its supposed to be a un-initialised variable
        # class getters in the current class have priority
        if self._getter(name) in cls.__dict__:
            value = self._set_and_get(name)
            self._indent-=1
            return value
            if 'method' in PROFILE:
                print "%sGetter of %s found in class %s" % (
                    self._indent*PROFILE_INDENT, self._getter(name), cls.__name__)
        elif name in cls.__dict__:
            value = self._get_or_set(name, cls.__dict__[name])
            self._indent-=1
            return value
            if 'method' in PROFILE:
                print "%sProperty %s found in class %s, with value %s" % (
                    self._indent*PROFILE_INDENT, name, cls.__name__, value)
        else: # something went wrong in the loop
            raise Exception("%sSomething went wrong in the loop")
        return value

    def is_getter(self, name):
        return name.find('get_') == 0

    def _get_from_classes(self, name):
        cls = self.__class__
        while not name in cls.__dict__:
            while not cls == object:
                cls = cls.__bases__.pop()
        return cls.__dict__[name]

    def _set_and_get(self, name):
        value = self._get(name)
        setattr(self, name, value)
        return value

    def _get(self, name):
        return getattr(self, self._getter(name))()

    def _getter(self, name):
        return 'get_' + name

    def _get_or_set(self, name, value):
        try:
            return getattr(self, name)
        except PropertyInitialiserMissing:
            setattr(self, name, value)
        return getattr(self, name, value)

    def _hasanyof(self, names):
        for name in names:
            if self._has(name):
                return True
        return False

    def _hasvalue(self, name):
        return name in self.__class__.__dict__

    def _has(self, name):
        if name in self.__class__.__dict__ \
            or name in self.__dict__ \
            or hasattr(self, self._getter(name)):
            return True
        return False

class jobject(ProgrammablePropertyInitialiser):
    pass

if TEST:
    class jtestA(jobject):
        testA=True
        def get_testD(self):
            return True
        def get_chain_Z(self):
            return 'Z'
    class jtestB(jtestA):
        testB=True
        def somemethod(self):
            self.somemethod_run = True
    class jtestBB(jtestA):
        testBB=True
        def get_testB(self):
            return True
        def get_testD(self):
            return False
    class jtestC(jtestB, jtestBB):
        testC=True
        def get_testB(self):
            return False
        def get_chain_W(self):
            return self.chain_X
    class jtestE(jtestC):
        def get_chain_Y(self):
            return self.chain_Z
        def get_chain_X(self):
            return self.chain_Y
        def do_testB(self):
            if test.testB != test.get_testB():
                print "!Got %s instead of expected %s for property %s" % (
                    test.testB, test.get_testB(), "testB")
                print "!This means that class variables are final."
    
    test = jtestE()
    if not jtestA.testA == test.testA \
        or not jtestBB.testBB == test.testBB \
        or not jtestC.testC == test.testC:
        print "!Simple class variable overloading fails"
    # make sure the most recent getter is ran
    if not test.testD == False:
        print "!Got %s instead of expected %s for property %s" % (
            test.testD, False, "testD")
    # this test demonstrates that you should use as much getters
    # as possible, and not define default values with class
    # variables.
    #
    # A getter hasn't priority over a parent's class-variable
    # because __getattr__ is not called in that case.
    test.do_testB()
    
    # make sure that we get exceptions right
    fail = True
    try:
        test.test_LOL
    except PropertyInitialiserMissing:
        fail = False
        # reset indentation
        test._indent=-1
    if fail:
        print "!Excepted a PropertyInitialiserMissing for test_LOL"

    test.test_LOL = "LOL"
    if not test.test_LOL == "LOL":
        print "!Can't even set a variable"

    if not test.chain_W == 'Z':
        print "!W problem"

    test.somemethod()
    if not test.somemethod_run:
        print "!Couldn't run regular method"
