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


class SingleDispatchClassDict(UserDict):
    def __init__(self):
        self.non_funcs = dict()
        super().__init__()

    def __setitem__(self, func_name, func):
        if inspect.isfunction(func):
            if func_name not in self:
                super().__setitem__(func_name, SingleDispatchMethodTree(default=func))  # first declaration. set default

            sig = inspect.signature(func)
            ann_sig = tuple(param.annotation for par_name, param in sig.parameters.items())
            self[func_name][ann_sig] = func
        else:
            self.non_funcs[func_name] = func


def single_dispatch_func(func_tree):
    @wraps(func_tree.default)
    def wrapped_func(*args, **kwargs):
        try:
            func = func_tree[args]
        except NoValidAnnotation:
            func = func_tree.default
        return func(*args, **kwargs)
    setattr(wrapped_func, 'func_tree', func_tree)
    return wrapped_func


class SingleDispatchMetaClass(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return SingleDispatchClassDict()

    def __new__(mcs, clsname, bases, clsdict):

        new_clsdict = dict()
        new_clsdict.update(clsdict.non_funcs)

        for func_name, func_tree in clsdict.items():
            # First method to be declared is considered the default method
            if func_tree.count == 1:
                new_clsdict[func_name] = func_tree.default
                continue

            new_clsdict[func_name] = single_dispatch_func(func_tree)


        clsobj = super().__new__(mcs, clsname, bases, new_clsdict)
        return clsobj