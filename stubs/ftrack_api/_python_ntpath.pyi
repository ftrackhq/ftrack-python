from genericpath import *
from _typeshed import Incomplete
from nt import _isdir as isdir

__all__ = [
    "normcase",
    "isabs",
    "join",
    "splitdrive",
    "split",
    "splitext",
    "basename",
    "dirname",
    "commonprefix",
    "getsize",
    "getmtime",
    "getatime",
    "getctime",
    "islink",
    "exists",
    "lexists",
    "isdir",
    "isfile",
    "ismount",
    "walk",
    "expanduser",
    "expandvars",
    "normpath",
    "abspath",
    "splitunc",
    "curdir",
    "pardir",
    "sep",
    "pathsep",
    "defpath",
    "altsep",
    "extsep",
    "devnull",
    "realpath",
    "supports_unicode_filenames",
    "relpath",
]

curdir: str
pardir: str
extsep: str
sep: str
pathsep: str
altsep: str
defpath: str
devnull: str

def normcase(s): ...
def isabs(s): ...
def join(a, *p): ...
def splitdrive(p): ...
def splitunc(p): ...
def split(p): ...
def splitext(p): ...
def basename(p): ...
def dirname(p): ...
def islink(path): ...

lexists = exists

def ismount(path): ...
def walk(top, func, arg) -> None: ...
def expanduser(path): ...
def expandvars(path): ...
def normpath(path): ...
def abspath(path): ...

realpath = abspath
supports_unicode_filenames: Incomplete

def relpath(path, start=...): ...

# Names in __all__ with no definition:
#   commonprefix
#   exists
#   getatime
#   getctime
#   getmtime
#   getsize
#   isfile
