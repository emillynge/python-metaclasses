from collections import UserDict, OrderedDict, Sequence, deque, defaultdict
import inspect
from functools import wraps, lru_cache, partial
from .utils import Options
from typing import List


class _ChainedProps:
    def __init__(self, opt: Options):
        assert isinstance(opt, Options)
        self.opt = opt
        self._property_cache = dict()
        self._property_stack = list()

    @lru_cache()
    def options_callback(self, prop_name):
        return partial(self.del_callback, prop_name)

    def del_callback(self, prop_name, key, value):
        delattr(self, prop_name)


class ChainedPropsMetaClass(type):
    """
    class that relies on a single Options dict provided at init for all property
    fetches.

    """

    def __new__(mcs, clsname, bases, clsdict):
        new_clsdict = dict()
        property_getters = dict()
        dependencies = defaultdict(set)

        for func_name, func in clsdict.items():
            if isinstance(func, property):
                getter = func.fget
                params = list(inspect.signature(getter).parameters.values())
                params.pop(0)
                deleters = func.fdel or list()
                for deleter in deleters:
                    dependencies[deleter].add(func_name)

                property_getters[func_name] = partial(mcs.getter, mcs, getter,
                                                      params, func_name,
                                                      dependencies)

            new_clsdict[func_name] = func

        for prop_name, getter in property_getters.items():
            new_clsdict[prop_name] = property(fget=getter,
                                              fdel=partial(mcs.deleter,
                                                           mcs,
                                                           prop_name,
                                                           dependencies))

        clsobj = super().__new__(mcs, clsname, bases, new_clsdict)
        return clsobj

    # noinspection PyProtectedMember
    def deleter(self, func_name, dependencies, instance: _ChainedProps):
        for dependency in dependencies[func_name]:
            delattr(instance, dependency)
        if func_name in instance._property_cache:
            del instance._property_cache[func_name]

    # noinspection PyProtectedMember
    def getter(self, wrapped, params, func_name, dependencies,
               instance: _ChainedProps):
        if instance._property_stack:
            dependencies[func_name].add(instance._property_stack[-1])


        if func_name in instance._property_cache:
            return instance._property_cache[func_name]
        instance._property_stack.append(func_name)
        try:
            args, kwargs = self._fetch_opts(instance, params, func_name)
            prop = wrapped(instance, *args, **kwargs)
        finally:
            instance._property_stack.remove(func_name)

        instance._property_cache[func_name] = prop
        return prop

    @staticmethod
    def _fetch_opts(instance: _ChainedProps,
                    parameters: List[inspect.Parameter],
                    func_name):
        kwargs = OrderedDict()
        args = list()
        for param in parameters:
            name = param.name

            # check if **kwargs
            if param.kind.name == 'VAR_KEYWORD':
                raise ValueError(
                    'Do not have **kwargs input types chained property'.format())


            # if no default
            elif param.default is inspect._empty:
                if name in instance.opt:
                    args.append(instance.opt[name])
                else:
                    raise ValueError(
                        'parameter "{}" used but is not specified in opts'.format(
                            name))

            # default present. input out own if present
            elif name in instance.opt:
                kwargs[name] = instance.opt[name]

            instance.opt.set_callback(name, instance.options_callback(func_name))

        return args, kwargs

    """
    def _get_constructors(self, constructor_names):
        for constructor in constructor_names:
            yield getattr(self, constructor)

    def construct(self, constructors):
        prev = None
        for constructor in self._get_constructors(constructors):
            kwargs = self._fetch_opts(constructor, prev=prev)
            try:
                prev = constructor(**kwargs)
            except Exception as e:
                raise ValueError('Exception during construction of {!r}'.format(constructor)) from e
        return prev
    """


class ChainedProps(_ChainedProps, metaclass=ChainedPropsMetaClass):
    pass
