from collections import (namedtuple, OrderedDict, defaultdict, UserDict)
import inspect
from functools import (lru_cache, partial, wraps)
from .utils import Options
from itertools import chain
from typing import List, Sequence, Union

GlobalFuncName = namedtuple('GlobalFuncName', 'cls_name func_name')
setattr(GlobalFuncName, '__repr__',
        lambda self: self.cls_name + '.' + self.func_name)


class IllegalConstruction(SyntaxError):
    pass


class DependencyDict(UserDict):
    def __init__(self, clsname):
        self.clsname = clsname
        super().__init__()
        super().__setitem__(clsname, defaultdict(set))

    def add_base(self, base: object):
        if hasattr(base, '_dependencies'):
            for _base, _dependencies in base._dependencies.super_items():
                super().__setitem__(_base, _dependencies)

    def get_func_dict(self):
        return super().__getitem__(self.clsname)

    def super_items(self):
        for base in self.keys():
            yield base, super().__getitem__(base)

    def __setitem__(self, dependency: GlobalFuncName, function: GlobalFuncName):
        """
        Assign value function as dependant on key function
        :param dependency: a function that is required by another function
        :param function: a function that requires a dependency
        :return:
        """
        try:
            self.__getitem__(dependency).add(function)

        except KeyError:
            raise KeyError(
                    "{1!r} cannot depend on {0!r}, {3} is not a subclass of {2}".format(
                            dependency, function, dependency.cls_name,
                            function.cls_name
                    ))

    def __getitem__(self, dependency: GlobalFuncName):
        """
        get all functions that depend on "dependency"
        :param dependency:
        :return: GlobalFuncName instance of a function that requires dependency
        """
        return super().__getitem__(dependency.cls_name)[dependency.func_name]


def args_from_opt(*non_opt_args: Sequence):
    """A decorator indicating a method which should take some or all of its
    input from self.opt: Options

    Requires that the metaclass is ChainedPropsMetaClass or derived from it.
    """
    def tagger(funcobj):
        funcobj.__args_from_opt__ = non_opt_args
        return funcobj
    return tagger


class _ChainedProps:
    _dependencies = DependencyDict(
        '_ChainedProps')  # <- Overwritten by metaclass!

    def __init__(self, opt: Options):
        assert isinstance(opt, Options)
        self.opt = opt
        self._property_cache = dict()
        self._property_stack = list()

    @lru_cache()
    def options_callback(self, prop_name):
        return partial(self.del_callback, prop_name)

    def del_callback(self, prop_name, key, value):
        self._prop_cache_delete(prop_name)

    # noinspection PyProtectedMember
    def _prop_cache_delete(self, func_descriptor):
        dependencies = self._dependencies
        delete_q = {func_descriptor}
        while delete_q:
            del_fun = delete_q.pop()

            # by induction, a property not in the cache would already have
            # deleted any dependants or not have created any.
            if del_fun not in self._property_cache:
                continue

            delete_q.update(dependencies[del_fun])
            self._property_cache.pop(del_fun)


class ChainedPropsMetaClass(type):
    """
    class that relies on a single Options dict provided at init for all property
    fetches.

    """

    def __new__(mcs, clsname, bases, clsdict):
        new_clsdict = dict()
        dependencies = DependencyDict(clsname)
        for base in bases:
            dependencies.add_base(base)

        new_clsdict['_dependencies'] = dependencies

        for func_name_local, func in clsdict.items():
            if isinstance(func, property):
                func_name_global = GlobalFuncName(clsname, func_name_local)
                getter = func.fget
                params = list(inspect.signature(getter).parameters.values())
                params.pop(0)
                new_get = partial(mcs.getter, mcs, getter,
                                  params, func_name_global)

                new_del = partial(mcs.deleter, func_name_global)
                new_clsdict[func_name_local] = property(fget=new_get,
                                                        fdel=new_del)
            elif hasattr(func, '__args_from_opt__'):
                if isinstance(func, (classmethod, staticmethod)):
                    raise IllegalConstruction('args_from_opts requires an '
                                              'instance to get opts from '
                                              'this cis incompatible with '
                                              'class- and staticmethods')
                non_opt_args = func.__args_from_opt__
                wrapper = mcs.args_from_opt(non_opt_args)
                new_clsdict[func_name_local] = wrapper(func)

            else:
                new_clsdict[func_name_local] = func

        clsobj = super().__new__(mcs, clsname, bases, new_clsdict)
        return clsobj

    @staticmethod
    def deleter(func_descriptor: GlobalFuncName, instance: _ChainedProps):
        instance._prop_cache_delete(func_descriptor)

    # noinspection PyProtectedMember
    def getter(self, wrapped, params, func_descriptor: GlobalFuncName,
               instance: _ChainedProps):

        dependencies = instance._dependencies
        assert isinstance(dependencies, DependencyDict)

        # if the property stack is non-empty this property has been requested
        # by another property. The immediate dependant property is the last
        # called in the stack
        if instance._property_stack:
            dependant = instance._property_stack[-1]
            # add current prop as dependency of dependant
            dependencies[func_descriptor].add(dependant)

        if func_descriptor in instance._property_cache:
            return instance._property_cache[func_descriptor]

        instance._property_stack.append(func_descriptor)
        try:
            args, kwargs = self._fetch_opts(instance, params, func_descriptor)
            prop = wrapped(instance, *args, **kwargs)
        finally:
            instance._property_stack.remove(func_descriptor)

        instance._property_cache[func_descriptor] = prop
        return prop

    @staticmethod
    def _fetch_opts(instance: _ChainedProps,
                    parameters: List[inspect.Parameter],
                    callback_func_name=None, ignore: Sequence[str]=tuple()):

        kwargs = OrderedDict()
        args = list()
        for param in parameters:
            name = param.name

            # check if **kwargs
            if param.kind.name == 'VAR_KEYWORD':
                raise IllegalConstruction(
                        'Do not have **kwargs input types chained property'.format())

            # if no default
            elif param.default is inspect._empty:
                if name in instance.opt:
                    args.append(instance.opt[name])
                elif name not in ignore:
                    raise ValueError(
                            'parameter "{}" used but is not specified in opts'.format(
                                    name))
                else:
                     args.append(None)

            # default present. input out own if present
            elif name in instance.opt:
                kwargs[name] = instance.opt[name]

            if callback_func_name:
                instance.opt.set_callback(name,
                                      instance.options_callback(callback_func_name))

        return args, kwargs

    @classmethod
    def args_from_opt(mcs, non_opt_args: Sequence):
        def wrapper(func):
            params = list(inspect.signature(func).parameters.values())
            params.pop(0)
            ignore = tuple()

            if len(non_opt_args) == 1 and isinstance(non_opt_args[0], int):
                params = params[non_opt_args[0]:]

                def mergeargs(args, optargs):
                    return chain(args, optargs)

            elif non_opt_args:
                param_names = list(param.name for param in params)
                idx = [-1] + [param_names.index(param) for param in non_opt_args] + [None]

                slices = [slice(i + 1,j) for i,j in zip(idx[:-1], idx[1:])]
                def yielder(args, optargs):
                    for opt_slice, arg in zip((optargs[s] for s in slices), args):
                        yield opt_slice
                        yield (arg,)

                    yield optargs[slices[-1]]

                def mergeargs(args, optargs):
                    return chain(*yielder(args, optargs))

                ignore = tuple(params[i].name for i in idx[1:-1])

            else:
                # No thrills wrapper
                @wraps(func)
                def wrapfun(instance):
                    optargs, optkwargs = mcs._fetch_opts(instance, params)
                    return func(instance, *optargs, **optkwargs)
                return wrapfun

            # more complex wrapper
            @wraps(func)
            def wrapfun(instance, *args, **kwargs):
                optargs, optkwargs = mcs._fetch_opts(instance, params,
                                                     ignore=ignore)
                optkwargs.update(kwargs)
                return func(instance, *mergeargs(args, optargs), **optkwargs)
            return wrapfun
        return wrapper

class ChainedProps(_ChainedProps, metaclass=ChainedPropsMetaClass):
    pass
