"""
Classes that are not metaclasses
"""
from collections import OrderedDict, defaultdict
from weakref import WeakSet

from argparse import ArgumentParser
from functools import partial
from itertools import chain


class FailAssert:
    def __init__(self, *fail_types):
        self.fail_types = fail_types if fail_types else [AssertionError]

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            raise AssertionError('Should have failed')

        if exc_type not in self.fail_types:
            raise exc_type(exc_val)

        return True


class Options(OrderedDict):
    """
    A simple argument parser that doubles as a dictionary

    dictionary members are automatically assigned short and long arguments

    callbacks can be assigned to a member such that changes will trigger it.
    NOTE: callbacks are stored as weak references and will disappear if the
    original callback is deleted
    """
    def __init__(self, *args, **kwargs):
        if '_make_called' not in kwargs:
            raise ValueError('Never call Options directly, use Options.make')
        else:
            kwargs.pop('_make_called')
        self._short_args = OrderedDict(h='help')
        self._argsparser = ArgumentParser()
        self._on_change_callbacks = defaultdict(WeakSet)
        super().__init__(*args, **kwargs)

    @staticmethod
    def _getter(key, self):
        return self[key]

    @staticmethod
    def _setter(key, self, value):
        self[key] = value

    def find_short_arg(self, key):
        orig_key = key
        key = key.replace('_', '')
        key = [k for k in ''.join([c + c.upper() for c in key])]
        shortarg = key.pop(0)

        while shortarg in self._short_args and key:
            shortarg = key.pop(0)

        if shortarg in self._short_args:
            return None
        self._short_args[shortarg] = orig_key
        return shortarg

    def set_callback(self, key, callback):
        self._on_change_callbacks[key].add(callback)

    def trigger_callbacks(self, key):
        for callback in self._on_change_callbacks[key]:
            callback(key, self[key])

    def __setitem__(self, key, value):
        if key not in self or not hasattr(self, key):
            if not isinstance(key, str):
                raise ValueError('option names must be of type string')
            setattr(self.__class__, key, property(partial(self._getter, key),
                                        partial(self._setter, key)))

            cli_key = key.replace('_', '-')
            short_arg = self.find_short_arg(key)
            if short_arg is not None:
                args = ['-' + short_arg]
            else:
                args = []
            args.append('--' + cli_key)

            arg = partial(self._argsparser.add_argument, *args, dest=key)
            kwargs = dict()
            if isinstance(value, dict):
                kwargs.update(value)
                value = value.get('default', None)
            else:
                kwargs['default'] = value

            if 'type' not in kwargs and value is not None:
                kwargs['type'] = type(value)
            action = arg(**kwargs)
            if hasattr(action, 'default') and action.default is not None:
                value = action.default

            if hasattr(action, 'type') and action.type is not None:
                kwargs['type'] = action.type

            if value is not None and 'type' in kwargs and \
                    not isinstance(value, kwargs['type']):
                value = kwargs['type'](value)

        trigger_callback = False
        if key in self:
            if key in self._on_change_callbacks and value != self[key]:
                trigger_callback = True

        super().__setitem__(key, value)
        if trigger_callback:
            self.trigger_callbacks(key)

    def parseargs(self, *args):
        if len(args) < 1:
            args = None
        else:
            args = [str(arg) for arg in args]
        return self._argsparser.parse_args(args=args, namespace=self)

    @classmethod
    def make(cls, *args, **kwargs):
        """
        Make a new instance of Options.
        Always use this method
        :param args:
        :param kwargs:
        :return:
        """
        class CustomOptions(cls):
            pass
        kwargs['_make_called'] = True
        return CustomOptions(*args, **kwargs)

    def copy(self):
        return self.make(self.items())

    def bind_copy_to_parser(self, subparser: ArgumentParser):
        opt = self.make()
        opt._argsparser = subparser
        for key, val in self.items():
            opt[key] = val
        return opt

    def update_if_present(self, namespace=None, **kwargs):
        if namespace is not None:
            args = [item for item in namespace.__dict__.items()]
        else:
            args = list()

        for key, val in chain(kwargs.items(), args):
            if key in self:
                self[key] = val