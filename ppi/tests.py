from django.test import TestCase

from jpic import ppi

ppi.ppi.PROFILE=('pri', 'loop', 'method')

class jtestA(ppi.ppi):
    testA=True
    def get_testD(self):
        # should not be run
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
        # should not be run
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

class ProgrammablePropertyInitialiserTest(TestCase):
    def test_instanciation_kwargs(self):
        test = jtestE(foo='bar')
        self.assertEqual('bar', test.foo, 
            'expected any keyword argument to be set as property')

    def test_class_variable_passing(self):
        test = jtestE()
        self.assertEqual(jtestA.testA, test.testA,
            'expected jtestE instance to have testA class variable')
        self.assertEqual(jtestBB.testBB, test.testBB,
            'expected jtestE instance to have testBB class variable')
        self.assertEqual(jtestC.testC, test.testC,
            'expected jtestE instance to have testC class variable')
    
    def test_deepest_getter(self):
        test = jtestE()
        self.assertFalse(test.testD, 'excepted testE instance to run the deepest getter for testD (from jtestBB)')

    def test_class_variables_priority_over_getters(self):
        """
        This test demonstrates that you should use as much getters
        as possible, and not define default values with class
        variables.
    
        A getter hasn't priority over a parent's class-variable
        because __getattr__ is not called in that case.
        """

        test = jtestE()
        self.assertNotEqual(test.testB, test.get_testB(),
            'excepted test.testB to not call the getter get_testB()'
        )
        self.assertEqual(test.testB, jtestB.testB,
            'excepted test.testB to equal class variable jtestB.testB'
        )
   
    def test_exception_throw(self):
        test = jtestE()
        fail = True
        
        try:
            test.test_UNDEFINED
        except ppi.PropertyInitialiserMissing:
            fail = False

            # reset profiler indentation
            test._indent =- 1

        self.assertFalse(fail, '''
            excepted getting an undefined, ungettable property to throw
            PropertyInitialiserMissing''')

    def test_bc_set_instance_property(self):
        test = jtestE()
        
        test.test_foo = 'bar'
        self.assertEqual(test.test_foo, 'bar', 
            'excepted to be at least able to set an instance property')

    def test_bc_set_class_property(self):
        test = jtestE()

        jtestE.test_bar = 'foo'
        self.assertEqual(test.test_bar, 'foo', 
            'excepted to be at least able to set a class property')

    def test_bc_run_instance_method(self):
        test = jtestE()

        test.somemethod()
        self.assertTrue(test.somemethod_run, 
            'excepted to be at least able to run an instance method')

    def test_chaining_getters(self):
        test = jtestE()

        self.assertEqual(test.chain_W, 'Z', 
            'excepted jtestA.get_chain_Z() to have the "last word"')
