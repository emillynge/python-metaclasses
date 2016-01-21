import sys

from argparse import ArgumentParser
from contextlib import redirect_stderr

from io import StringIO

from elymetaclasses.utils import (Options, FailAssert)

class TestFailAssert:
    def test_fail(self):
        with FailAssert():
            assert 1==2

        with FailAssert(AssertionError):
            assert 1==2

        with FailAssert(AssertionError, ValueError):
            assert 1==2
            raise ValueError()

    def test_nofail(self):
        try:
            with FailAssert():
                pass
            raise AssertionError('Should have failed')
        except AssertionError:
            pass

    def test_unhandled_exc(self):
        try:
            with FailAssert():
                raise ValueError('pass through failassert')
            raise AssertionError('Should have failed')
        except ValueError:
            pass


class TestOptions:
    def test_make(self):
        with FailAssert(ValueError):
            Options()

        assert isinstance(Options.make(), Options)
        opt = Options.make([('foo', 'bar')], hej='med')
        assert opt.foo == 'bar'
        assert opt['hej'] == 'med'


    def test_mangling(self):
        opt1 = Options.make([('foo', 'bar')], hej='med')
        opt2 = Options.make([('foo', 'mi')], nothere='dig')

        assert hasattr(opt1, 'foo')
        assert not hasattr(opt2, 'hej')
        assert not hasattr(opt1, 'nothere')
        assert opt1.foo == 'bar'
        assert opt2.foo == 'mi'

    def test_shortargs(self):
        opt1 = Options.make([('foo', 'bar'), ('fooo', 'baar'),
                             ('hej',10), ('heej','med'), ('heeej','dig'),
                             ('hejj',1), ('hejjj',2), ('hejjjj',3)])
        opt1.parseargs('-H10', '-e', 'meed', '-E', 'mig',
                       '-f', 'mar', '-F', 'maar', '-J4', '--hejjjj', 6)
        #simple shortargs
        assert opt1.hej == 10
        assert opt1.heej == 'meed'
        assert opt1.heeej == 'mig'
        assert opt1.hejjj == 4

        # longargs
        assert opt1.hejjjj == 6

        # input specs to argparser
        opt1['bar'] = {'type': float, 'default': 10}
        assert opt1.bar == 10

        # typecasting
        assert isinstance(opt1.bar, float)
        opt1.parseargs('-b11')
        assert opt1.bar == 11
        assert isinstance(opt1.bar, float)

        # opt not reset
        assert opt1.hejjjj == 6

        # true/false
        opt1['tf'] = {'action': 'store_true'}
        assert opt1.tf is False

        opt1.parseargs('-b10')
        assert opt1.tf is False
        opt1.parseargs('-t')
        assert opt1.tf is True


    def test_callbacks(self):
        mydict = {'change': False}
        def callback(key, value):
            mydict['change'] = key

        opt1 = Options.make([('foo', 'bar')], hej='med')
        opt1.set_callback('foo', callback)

        assert mydict['change'] is False

        # callback on setattr
        opt1.foo = 'mar'
        assert mydict['change'] == 'foo'
        mydict['change'] = False

        # callback on parse
        opt1.parseargs('-fbar')
        assert mydict['change'] == 'foo'

        # no callback when function is removed
        del callback
        mydict['change'] = False
        opt1.foo = 'mar'
        assert mydict['change'] is False


    def test_add2parser(self):
        opt1 = Options.make([('foo', 'bar')], hej='med')
        main_parser = ArgumentParser()
        actions_group = main_parser.add_argument_group('foo')
        actions_group.add_argument('-b', '--bar', default='foo')
        opt2 = opt1.bind_copy_to_parser(main_parser.add_argument_group('bar'))


        # main parser
        args = main_parser.parse_args(['-fmar'])
        assert args.foo == 'mar'
        assert args.bar == 'foo'

        assert opt2.foo == 'bar'

        opt2.update_if_present(foo='mar', nothere=False)
        assert args.foo == 'mar'
        assert 'nothere' not in opt2

        opt2.foo = 'bar'
        opt2.update_if_present(args)
        assert opt2.foo == 'mar'
        assert opt1.foo == 'bar'

        opt2.foo = 'bar'
        main_parser.parse_args(['-fmar'], namespace=opt2)
        assert args.foo == 'mar'
        assert 'nothere' not in opt2

    def test_copy(self):
        opt1 = Options.make([('foo', 'bar')], hej='med', dig={'action': 'store_true'})
        opt2 = opt1.copy()

        #TODO copies should copy actions, not values
        with FailAssert(SystemExit):
            with redirect_stderr(StringIO()):
                opt2.parseargs('-d')

        opt2.parseargs('-d', True)
        assert opt2.dig is True
        assert opt1.dig is False





