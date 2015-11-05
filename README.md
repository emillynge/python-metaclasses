# python-metaclasses
A collection of useful metaclasses for python

## Single Dispatch
Inheriting the metaclass SingleDispatchMetaClass makes it possible to use function annotations to overload a method

```python
from elymetaclasses import SingleDispatchMetaClass

class MyClass(metaclass=SingleDispatchMetaClass):
    def myfunc(first, second)
        """
            Default method
        """
        return first

    def myfunc(first: int, second: int)
            """
                Invoked if both arguments are of type int
            """
            return first * second
    
    def myfunc(first, second: int)
            """
                invoked if second is of type int but first is not
            """
            return second * 2
```
An overloaded method will only be called if all annotated arguments passes: isinstance(arg, annotation).
Arguments with no annotation are "wild cards", i.e they will match any input.
Arguments are matched from left to right.
If no methods matches the function signatures the first method declared in the class body will be called.

### Inheritance
If a baseclass 
