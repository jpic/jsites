from exceptions import *

class ProgrammablePropertyInitialiser(object):
    
    #PROFILE=('pri', 'loop', 'method')
    PROFILE=()
    PROFILE_INDENT='    '
    
    _indent=-1
    _security_stack=[]

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __getattr__(self, name):
        # pass out if its not something we want to touch
        if name[:1] == '_':
            return super(ProgrammablePropertyInitialiser, self).__getattribute__(name)
        self._indent+=1
        if 'pri' in self.__class__.PROFILE:
            print "%s- Programmable variable requested: %s" % (self._indent*self.__class__.PROFILE_INDENT, name)

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
                    if 'stack' in self.__class__.PROFILE:
                        print "%sNew stack of classes to check %s" % (
                            self._indent*self.__class__.PROFILE_INDENT, unicode(stack))
                # get next parent
                cls = stack[item]
                item+= 1
                if 'loop' in self.__class__.PROFILE:
                    print "%sChecking for %s (#%s) or %s() in %s" % (
                        self._indent*self.__class__.PROFILE_INDENT, name, item,  self._getter(name), cls)

        # its supposed to be a un-initialised variable
        # class getters in the current class have priority
        if self._getter(name) in cls.__dict__:
            # this stack will be used to figure if getters are calling each others
            # to prevent user desing from sucking
            if self._security_stack.count(name) < 2:
                self._security_stack.append(name)
            else:
                # clean before showing
                defect = []
                for item in self._security_stack:
                    if self._security_stack.count(item) > 1 and self._getter(item) not in defect:
                        defect.append(self._getter(item))
                raise Exception("Recursion detected in "+unicode(self)+" between getters: " + unicode(defect) + ", full _security_stack: " + unicode(self._security_stack) )
            value = self._set_and_get(name)
            
            # Got the value! we're safe
            while name in self._security_stack:
                self._security_stack.remove(name)
            
            if not self.__class__.PROFILE:
                return value
            
            self._indent-=1
            
            if 'method' in self.__class__.PROFILE:
                print "%sGetter of %s found in class %s" % (
                    self._indent*self.__class__.PROFILE_INDENT, self._getter(name), cls.__name__)
        
        elif name in cls.__dict__:
            value = self._get_or_set(name, cls.__dict__[name])
            
            if not self.__class__.PROFILE:
                return value
            
            self._indent-=1

            if 'method' in self.__class__.PROFILE:
                print "%sProperty %s found in class %s, with value %s" % (
                    self._indent*self.__class__.PROFILE_INDENT, name, cls.__name__, value)
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

