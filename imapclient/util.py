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
