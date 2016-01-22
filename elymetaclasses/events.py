from collections import (namedtuple, OrderedDict, defaultdict, UserDict)
import inspect
from functools import (lru_cache, partial)
from .utils import Options
from typing import List

GlobalFuncName = namedtuple('GlobalFuncName', 'cls_name func_name')
setattr(GlobalFuncName, '__repr__',
        lambda self: self.cls_name + '.' + self.func_name)


class DependencyDict(UserDict):
    def __init__(self, clsname):
        self.clsname = clsname
        super().__init__()
        super().__setitem__(clsname, defaultdict(set))

    def add_base(self, base: object):
        if hasattr(base, '_dependencies'):
            super().__setitem__(base.__name__,
                                base._dependencies.get_func_dict())

    def get_func_dict(self):
        return super().__getitem__(self.clsname)

    def __setitem__(self, dependency: GlobalFuncName, function: GlobalFuncName):
        """
        Assign value function as dependant on key function
        :param dependency: a function that is required by another function
        :param function: a function that requires a dependency
        :return:
        """
        try:
            super().__setitem__(dependency, function)

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

            instance.opt.set_callback(name,
                                      instance.options_callback(func_name))

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
