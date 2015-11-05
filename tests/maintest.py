__author__ = 'emil'
from elymetaclasses import SingleDispatchMetaClass

class Dummy(object):
    pass

class Dummy2(object):
    pass

class TestSingleDispatch(metaclass=SingleDispatchMetaClass):
    def myfunc2(self, first: Dummy, second:Dummy):
        return 'default'

    def myfunc2(self, first, second):               # function with no annotation is default in practice no matter placement
            return 'empty'

    def myfunc(self, first: Dummy, second:Dummy):   # first declaration becomes default
        return 'default'

    def myfunc(self, first: int, second:str):
        return 'int', 'str'

    def myfunc(self, first, second:str):
            return 'empty', 'str'

    def test_default(self):
        assert self.myfunc(Dummy2(), Dummy2()) == 'default'
        assert self.myfunc2(Dummy2(), Dummy2()) == 'empty'

    def test_int_str(self):
        assert self.myfunc(1, 'hi') == ('int', 'str')

    def test_empty_str(self):
        assert self.myfunc(Dummy2(), 'hi') == ('empty', 'str')

    @staticmethod
    def mystaticfunc(first, second):
        return 'default'

    @staticmethod
    def mystaticfunc(first: int, second):
        return 'int', 'empty'

    def test_static(self):
        assert self.mystaticfunc(1, 'hi') == ('int', 'empty')
