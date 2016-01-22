__author__ = 'emil'
from collections import UserDict, OrderedDict, Sequence, deque
import inspect
from functools import wraps


class NoValidAnnotation(TypeError):
    pass


class SingleDispatchMethodTree(OrderedDict):
    def __init__(self, default=None, fun_type='method', **kwargs):
        self.func = None
        self.fun_type = fun_type
        self.default = default
        super().__init__(**kwargs)

    @property
    def count(self):
        count = 0
        for val in self.values():
            count += val.count

        if self.func:
            count += 1
        return count

    def __setitem__(self, annotations: Sequence, func):
        if annotations:                                 # Still more annotations to put into tree
            annotations = deque(annotations)
            annotation = annotations.popleft()          # take leftmost annotation out
            item = self.get(annotation, self.__class__())
            item[annotations] = func                    # assign remaining annotations to new dict with func
            super().__setitem__(annotation, item)

        else:
            self.func = func

    def __getitem__(self, args: Sequence):
        if args:
            args = deque(args)
            arg = args.popleft()

            for annotation, sub_dict in self.items():
                try:
                    if isinstance(arg, annotation):
                        return sub_dict[args]
                except NoValidAnnotation:
                    print('hi')
                    pass
        elif self.func is not None:
            return self.func

        if inspect._empty in self:
            return super().__getitem__(inspect._empty)[args]
        raise NoValidAnnotation()

def get_annotations(func):
    sig = inspect.signature(func)
    return tuple(param.annotation for par_name, param in sig.parameters.items())


class SingleDispatchClassDict(UserDict):
    def __init__(self):
        self.non_funcs = dict()
        super().__init__()

    def __setitem__(self, func_name, func):
        fun_type = None
        if isinstance(func, staticmethod):
            fun_type = 'static'
            annotations = get_annotations(func.__func__)
            func = func.__func__

        elif isinstance(func, classmethod):
            fun_type = 'class'
            annotations = get_annotations(func.__func__)
            func = func.__func__

        elif inspect.isfunction(func):
            fun_type = 'standard'
            annotations = get_annotations(func)

        if fun_type:
            if func_name not in self:
                super().__setitem__(func_name, SingleDispatchMethodTree(default=func, fun_type=fun_type))  # first declaration. set default

            self[func_name][annotations] = func
        else:
            self.non_funcs[func_name] = func


def single_dispatch_func(func_trees):
    default_func = func_trees[0].default
    fun_type = func_trees[0].fun_type

    @wraps(default_func)
    def wrapped_func(*args, **kwargs):
        for func_tree in func_trees:
            try:
                func = func_tree[args]
                break
            except NoValidAnnotation:
                pass
        else:
            func = default_func

        return func(*args, **kwargs)
    if fun_type == 'static':
        wrapped_func = staticmethod(wrapped_func)
    elif fun_type == 'class':
        wrapped_func = classmethod(wrapped_func)

    setattr(wrapped_func, 'func_tree', func_trees)
    return wrapped_func


class SingleDispatchMetaClass(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return SingleDispatchClassDict()

    def __new__(mcs, clsname, bases, clsdict):

        new_clsdict = dict()
        new_clsdict.update(clsdict.non_funcs)

        for func_name, func_tree in clsdict.items():
            inherited_funcs = [getattr(base, func_name) for base in bases if hasattr(base, func_name) and
                               issubclass(base.__class__, mcs)]
            func_trees = [func_tree]

            for func in inherited_funcs:
                if hasattr(func, 'func_tree'):
                    func_trees.extend(func.func_tree)
                    continue
                _func_tree = SingleDispatchMethodTree()
                _func_tree[get_annotations(func)] = func

                func_trees.append(_func_tree)

            # First method to be declared is considered the default method
            if len(func_trees) == 1 and func_tree.count == 1:
                new_clsdict[func_name] = func_tree.default
                continue

            new_clsdict[func_name] = single_dispatch_func(func_trees)


        clsobj = super().__new__(mcs, clsname, bases, new_clsdict)
        return clsobj


class SingleDispatch(metaclass=SingleDispatchMetaClass):
    pass

class LastResort:
    """
    Will match no annotations
    """
    pass

def type_assert(func, annotations):

    @wraps(func)
    def wrapped(*args, **kwargs):
        for arg, ann in zip(args, annotations):
            if ann != inspect._empty:
                assert isinstance(arg, ann)
        return func(*args, *kwargs)
    return wrapped


class TypeAssertMetaClass(type):
    def __new__(mcs, clsname, bases, clsdict):
        new_clsdict = dict(clsdict)
        for func_name, func in clsdict.items():
            if not inspect.isfunction(func):
                continue
            ann = get_annotations(func)
            if all([an == inspect._empty for an in ann]):
                new_clsdict[func_name] = func
            else:
                new_clsdict[func_name] = type_assert(func, ann)

        clsobj = super().__new__(mcs, clsname, bases, new_clsdict)
        return clsobj


