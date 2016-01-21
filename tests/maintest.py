__author__ = 'emil'
from elymetaclasses import *
from elymetaclasses.utils import FailAssert

class Dummy(object):
    pass

class Dummy2(object):
    pass


class AuxSingleDispatch1(metaclass=SingleDispatchMetaClass):
    def inherited_func(self, arg: tuple):
        return 'tuple'


class AuxSingleDispatch2(AuxSingleDispatch1):
    def inherited_func(self, arg: float):
        return 'float'


class AuxSingleDispatch3:
    def inherited_func(self, arg: Dummy):
        return 'Dummy'


class AuxSingleDispatch(AuxSingleDispatch2, AuxSingleDispatch3):
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

    @staticmethod
    def mystaticfunc(first, second):
        return 'default'

    @staticmethod
    def mystaticfunc(first: int, second):
        return 'int', 'empty'

    def inherited_func(self, arg: int):
        return 'default'

    def inherited_func(self, arg: str):
        return 'str'

    @classmethod
    def myclassmethod(cls, first, second):
        return cls.__name__

    @classmethod
    def myclassmethod(cls, first: int, second):
        return 'int', 'empty'


class TestSingledispatch:
    sd = AuxSingleDispatch()
    #def __init__(self):
    #    self.sd = None#AuxSingleDispatch()
    #    super(TestSingledispatch, self).__init__()

    def test_default(self):
        assert self.sd.myfunc(Dummy2(), Dummy2()) == 'default'
        assert self.sd.myfunc2(Dummy2(), Dummy2()) == 'empty'

    def test_int_str(self):
        assert self.sd.myfunc(1, 'hi') == ('int', 'str')

    def test_empty_str(self):
        assert self.sd.myfunc(Dummy2(), 'hi') == ('empty', 'str')

    def test_default_inherited(self):
        assert self.sd.inherited_func(Dummy2()) == 'default'

    def test_reach_inherited(self):
        assert self.sd.inherited_func(2.2) == 'float'

    def test_reach_inherited_deep(self):
        assert self.sd.inherited_func((2.2,)) == 'tuple'

    def test_do_not_reach_inherited(self):
        assert self.sd.inherited_func(Dummy()) != 'Dummy'

    def test_static(self):
        assert self.sd.mystaticfunc(1, 'hi') == ('int', 'empty')

    def test_static_default(self):
        assert self.sd.mystaticfunc('hej', 1) == 'default'

    def test_classmethod(self):
        assert self.sd.myclassmethod(1, 'hi') == ('int', 'empty')

    def test_classmethod_default(self):
        assert self.sd.myclassmethod('hej', 1) == self.sd.__class__.__name__




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


class AuxHooked0:
    pass


class AuxHooked1(HookedBase):
    subclasshooks = ['goose', 'typing']
    subclassregs = [AuxHooked0, list]


class AuxHooked2:
    def goose(self):
        pass


class AuxHooked3(AuxHooked2):
    def typing(self):
        pass


class AuxHooked4(list):
    pass


class AuxHooked5(AuxHooked1):
    subclasshooks = ['anothergoose']
    subclassregs = [int]


class AuxHooked6(AuxHooked3):
    def anothergoose(self):
        pass


class TestHooked:
    def test_regs(self):
        assert isinstance(AuxHooked0(), AuxHooked1)
        assert isinstance(AuxHooked4(), AuxHooked1)

    def test_goosetype(self):
        assert not isinstance(AuxHooked2(), AuxHooked1)
        assert isinstance(AuxHooked3(), AuxHooked1)

    def test_notinstance(self):
        assert not isinstance(str, AuxHooked1)

    def test_inheritance(self):
        assert not isinstance(AuxHooked3(), AuxHooked5)
        assert isinstance(AuxHooked6(), AuxHooked5)

        assert isinstance(AuxHooked4(), AuxHooked5)
