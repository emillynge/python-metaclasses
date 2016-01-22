from elymetaclasses.utils import FailAssert, Options
from elymetaclasses.events import ChainedProps
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

class SuperChained(Chained):
    @property
    def test(self):
        return super().test + 'super'

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