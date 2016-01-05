__author__ = 'emil'
from elymetaclasses import *

class Dummy(object):
    pass

class Dummy2(object):
    pass


class AuxSingleDispatch(metaclass=SingleDispatchMetaClass):
    def inherited_func(self, arg: tuple):
        return 'tuple'


class AuxSingleDispatch2(AuxSingleDispatch):
    def inherited_func(self, arg: float):
        return 'float'


class AuxSingleDispatch3:
    def inherited_func(self, arg: Dummy):
        return 'Dummy'


class TestSingleDispatch(AuxSingleDispatch2, AuxSingleDispatch3):
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

    def inherited_func(self, arg: int):
        return 'default'

    def inherited_func(self, arg: str):
        return 'str'

    def test_default_inherited(self):
        assert self.inherited_func(Dummy2()) == 'default'

    def test_reach_inherited(self):
        assert self.inherited_func(2.2) == 'float'

    def test_reach_inherited_deep(self):
        assert self.inherited_func((2.2,)) == 'tuple'

    def test_do_not_reach_inherited(self):
        assert self.inherited_func(Dummy()) != 'Dummy'


class FailAssert:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            raise AssertionError('Should have failed')

        if exc_type != AssertionError:
            raise exc_type(exc_val)

        return True


class TestTypeAssert(metaclass=TypeAssertMetaClass):
    def myfunc(self, first:int):
        return "success"

    def myfunc2(self, first):
        return "success"

    def myfunc3(self, first, second: int):
        return "success"

    def test_simple(self):
        assert self.myfunc(1) == 'success'
        with FailAssert():
            self.myfunc(1.5)


    def test_no_check(self):
        assert self.myfunc2(Dummy()) == 'success'

    def test_check_second(self):
        assert self.myfunc3(Dummy(), 1) == 'success'
        with FailAssert():
            self.myfunc3(Dummy(), None)
