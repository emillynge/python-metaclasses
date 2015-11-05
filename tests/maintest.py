__author__ = 'emil'
from elymetaclasses import SingleDispatchMetaClass

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
