import logging
from typing import Iterator, Optional, Tuple, Union
from . import exceptions
logger = logging.getLogger(__name__)
_TupleAtomPart = Union[None, int, bytes]
_TupleAtom = Tuple[Union[_TupleAtomPart, '_TupleAtom'], ...]

from .exceptions import IMAPProtocolError

def assert_imap_protocol(condition, message):
    """Assert that the condition is true, raising an IMAPProtocolError otherwise."""
    if not condition:
        raise IMAPProtocolError(message)

def to_unicode(s):
    """Convert a bytes object to a unicode string."""
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return s

def chunk(lst, size):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def to_bytes(s):
    """Convert a string to bytes."""
    if isinstance(s, str):
        return s.encode('utf-8')
    return s
