from elymetaclasses.utils import FailAssert, Options
from elymetaclasses.events import ChainedProps, IllegalConstruction, GlobalFuncName, args_from_opt
import abc
from collections import defaultdict

changes = defaultdict(int)

class Chained(ChainedProps):
    @property
    def test(self, hej, med='dig'):
        changes['test'] += 1
        return hej + med

    @property
    def test2(self, hej, med='mig'):
        changes['test2'] += 1
        return self.test + med

    @property
    def test3(self, hej):
        changes['test3'] += 1
        return self.test + hej

    @args_from_opt(1)
    def intmethod(self, dynarg, hej, med='me'):
        return dynarg + hej + med

    @args_from_opt('dynarg')
    def firstmethod(self, dynarg, hej, med='me'):
        return dynarg + hej + med

    @args_from_opt('hej')
    def secondmethod(self, dynarg, hej, med='me'):
        return dynarg + hej + med

    @args_from_opt(0)
    def kwargmethod(self, dynarg, hej, med='me'):
        return dynarg + hej + med

    @args_from_opt()
    def nothrill(self, dynarg, hej, med='me'):
        return dynarg + hej + med

class SuperChained(Chained):
    @property
    def test(self):
        return super().test + 'super'


class FailChained(ChainedProps):
    @property
    def kwarg_fun(self, **wrong):
        return False

    @property
    def missing_params(self, nothere):
        return False

class TestChained:
    opt1 = Options.make(hej='foo', med='bar')
    opt2 = Options.make(hej='mar')

    def test_init(self):
        chained = Chained(self.opt1)
        changes['test'] = 0

        # normal
        assert chained.test == 'foobar'
        assert changes['test'] == 1

        # use cache
        assert chained.test == 'foobar'
        assert changes['test'] == 1

    def test_del(self):
        chained = Chained(self.opt1)
        changes['test'] = 0

        assert chained.test2 == 'foobarbar'
        self.opt1.hej = 'boo'
        assert chained.test2 == 'boobarbar'

        assert chained.test3 == 'boobarboo'
        self.opt1.med = 'far'
        assert chained.test3 == 'boofarboo'

        # test direct deletion
        changes['test'] = 0
        del chained.test
        chained.test
        assert changes['test'] == 1

    def test_super(self):
        chained = SuperChained(self.opt1)
        changes['test'] = 0
        self.opt1.hej = 'foo'
        self.opt1.med = 'bar'

        # super get works
        assert chained.test == 'foobarsuper'

        # super depend works
        self.opt1.hej = 'boo'
        assert chained.test == 'boobarsuper'

    def test_fail(self):
        with FailAssert(IllegalConstruction):
            FailChained(self.opt1).kwarg_fun

        with FailAssert(ValueError):
            FailChained(self.opt1).missing_params

        with FailAssert(KeyError):
            chained = Chained(self.opt1)
            f1 = GlobalFuncName('Chained', 'test')
            f2 = GlobalFuncName('SuperChained', 'test')
            # try to set f2 as a dependency of f1
            chained._dependencies[f2] = f1

        with FailAssert(IllegalConstruction):
            class Failer(ChainedProps):
                @args_from_opt()
                @staticmethod
                def failer():
                    pass

        with FailAssert(IllegalConstruction):
            class Failer(ChainedProps):
                @args_from_opt()
                @classmethod
                def failer(cls):
                    pass



    def test_args_from_opts_decorator(self):
        chained = Chained(self.opt1)
        self.opt1.hej = 'foo'
        self.opt1.med = 'bar'

        assert chained.intmethod('hey') == 'heyfoobar'
        assert chained.firstmethod('hey') == 'heyfoobar'
        with FailAssert(ValueError):
            assert chained.secondmethod('hey') == 'heyfoobar'

        opt2 = self.opt1.copy()
        opt2['dynarg'] = 'dyn'
        chained = Chained(opt2)
        assert chained.secondmethod('hey') == 'dynheybar'
        assert chained.kwargmethod() == 'dynfoobar'
        assert chained.kwargmethod(med='boo') == 'dynfooboo'
        assert chained.nothrill() == 'dynfoobar'
