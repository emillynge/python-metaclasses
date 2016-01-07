from abc import ABCMeta
from collections import Iterable


def register_subclasses(klass: ABCMeta, subclassregs: Iterable):
    for subclass in subclassregs:
        klass.register(subclass)
    return klass


class HookedMetaClass(ABCMeta):
    """ Provides goosetyping by inhereting subclass hooks defined in bases"""
    def __new__(mcs,  name, bases, namespace):
        subclasshooks = set(namespace.pop('subclasshooks', list()))
        subclassregs = set(namespace.pop('subclassregs', list()))

        for base in bases:
            subclasshooks.update(base.__dict__.get('_subclasshooks', set()))
            subclassregs.update(base.__dict__.get('_subclassregs', set()))

        @classmethod
        def __subclasshook__(cls, C):
            if all(any(method in B.__dict__ for B in C.__mro__)
                   for method in subclasshooks):
                return True
            return NotImplemented

        namespace['_subclasshooks'] = subclasshooks
        namespace['_subclassregs'] = subclassregs
        namespace['__subclasshook__'] = __subclasshook__
        return register_subclasses(super().__new__(mcs, name, bases, namespace),
                                   subclassregs)


class HookedBase(metaclass=HookedMetaClass):
    subclasshooks = list()
    subclassregs = list()