__author__ = 'emil'
from collections import UserDict, OrderedDict, Sequence, deque
import inspect
from functools import wraps


class NoValidAnnotation(TypeError):
    pass


class SingleDispatchMethodTree(UserDict):
    def __init__(self, default=None, **kwargs):
        self.func = None
        self.default = default
        super().__init__(**kwargs)

    @property
    def count(self):
        count = 0
        for val in self.data.values():
            count += val.count

        if self.func:
            count += 1
        return count

    def __setitem__(self, annotations: Sequence, func):
        if annotations:                                 # Still more annotations to put into tree
            annotations = deque(annotations)
            annotation = annotations.popleft()          # take leftmost annotation out
            item = self.data.get(annotation, self.__class__())
            item[annotations] = func                    # assign remaining annotations to new dict with func
            super().__setitem__(annotation, item)

        else:
            self.func = func

    def __getitem__(self, args: Sequence):
        if not args:
            return self.func

        args = deque(args)
        arg = args.popleft()

        for annotation, sub_dict in self.data.items():
            try:
                if isinstance(arg, annotation):
                    return sub_dict[args]
            except NoValidAnnotation:
                print('hi')
                pass


        if inspect._empty in self.data:
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
        if inspect.isfunction(func):
            if func_name not in self:
                super().__setitem__(func_name, SingleDispatchMethodTree(default=func))  # first declaration. set default

            self[func_name][get_annotations(func)] = func
        else:
            self.non_funcs[func_name] = func


def single_dispatch_func(func_trees):
    default_func = func_trees[0].default

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
            inherited_funcs = [getattr(base, func_name) for base in bases if hasattr(base, func_name)]
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