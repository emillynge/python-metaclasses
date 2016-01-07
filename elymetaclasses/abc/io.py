from .base import HookedMetaClass
from abc import abstractmethod
from collections.abc import *
from io import TextIOBase as _TextIOBase
from io import TextIOWrapper as _TextIOWrapper
from io import StringIO as _StringIO
from io import BytesIO as _BytesIO
from _pyio import TextIOWrapper, TextIOBase, StringIO, BytesIO


class IOBase(metaclass=HookedMetaClass):
    subclasshooks = ['close']
    subclassregs = [_TextIOBase, _TextIOWrapper, TextIOBase, TextIOWrapper, _StringIO, _BytesIO, StringIO, BytesIO]

    @abstractmethod
    def close(self):
        pass


class InputStream(IOBase):
    subclasshooks = ['read']

    @abstractmethod
    def read(self, size=-1) -> Sequence:
        pass


class OutputStream(IOBase):
    subclasshooks = ['write']

    @abstractmethod
    def write(self, s) -> int:
        pass


class SeekableStream(IOBase):
    subclasshooks = ['seek', 'tell']

    @abstractmethod
    def seek(self, cookie, whence=0) -> int:
        pass

    @abstractmethod
    def tell(self) -> int:
        pass

class SeekableInputStream(InputStream, SeekableStream):
    pass

class SeekableOutputStream(OutputStream, SeekableStream):
    pass

class IOStream(InputStream, OutputStream):
    pass

class SeekableIOStrean(SeekableInputStream, SeekableOutputStream):
    pass
