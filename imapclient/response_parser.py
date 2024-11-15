"""Parsing for IMAP command responses with focus on FETCH responses as
returned by imaplib.

Initially inspired by http://effbot.org/zone/simple-iterator-parser.htm
"""

import datetime
import re
from collections import defaultdict
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from .datetime_util import parse_to_datetime
from .exceptions import ProtocolError
from .response_lexer import TokenSource
from .response_types import BodyData, Envelope, SearchIds
from .typing_imapclient import _Atom

__all__ = ["parse_response", "parse_message_list"]


def parse_response(data: List[bytes]) -> Tuple[_Atom, ...]:
    """Pull apart IMAP command responses.

    Returns nested tuples of appropriately typed objects.
    """
    lexer = TokenSource(data)
    return tuple(_parse_tokens(lexer))


def _parse_tokens(lexer: TokenSource) -> Iterator[Union[str, int, bytes, Tuple[Any, ...]]]:
    for token in lexer:
        if token == b"(":
            yield tuple(_parse_tokens(lexer))
        elif token == b")":
            return
        elif isinstance(token, bytes):
            yield token.decode("ascii")
        else:
            yield token


_msg_id_pattern = re.compile("(\\d+(?: +\\d+)*)")


def parse_message_list(data: List[Union[bytes, str]]) -> SearchIds:
    """Parse a list of message ids and return them as a list.

    parse_response is also capable of doing this but this is
    faster. This also has special handling of the optional MODSEQ part
    of a SEARCH response.

    The returned list is a SearchIds instance which has a *modseq*
    attribute which contains the MODSEQ response (if returned by the
    server).
    """
    data = [item.decode("ascii") if isinstance(item, bytes) else item for item in data]
    joined_data = " ".join(str(item) for item in data)
    match = _msg_id_pattern.match(joined_data)
    if not match:
        raise ProtocolError("Invalid message list: {}".format(joined_data))

    ids = [int(n) for n in match.group(1).split()]
    modseq = None
    if "MODSEQ" in data:
        modseq_index = data.index("MODSEQ") + 1
        if modseq_index < len(data):
            modseq = int(data[modseq_index])

    return SearchIds(ids, modseq)


_ParseFetchResponseInnerDict = Dict[
    bytes, Optional[Union[datetime.datetime, int, BodyData, Envelope, _Atom]]
]


def parse_fetch_response(
    text: List[bytes], normalise_times: bool = True, uid_is_key: bool = True
) -> defaultdict[int, _ParseFetchResponseInnerDict]:
    """Pull apart IMAP FETCH responses as returned by imaplib.

    Returns a dictionary, keyed by message ID. Each value a dictionary
    keyed by FETCH field type (eg."RFC822").
    """
    response = defaultdict(dict)
    lexer = TokenSource(text)

    for msg_id, fetch_data in _parse_fetch_pairs(lexer):
        msg_response = _ParseFetchResponseInnerDict()
        for field, value in fetch_data:
            field = field.upper()
            if field == b"UID" and uid_is_key:
                msg_id = value
            elif field in (b"INTERNALDATE", b"ENVELOPE"):
                msg_response[field] = _parse_fetch_field(field, value, normalise_times)
            else:
                msg_response[field] = value
        response[msg_id] = msg_response

    return response


def _parse_fetch_pairs(
    lexer: TokenSource,
) -> Iterator[Tuple[int, List[Tuple[bytes, Any]]]]:
    """Parse fetch pairs from the lexer."""
    while True:
        try:
            msg_id = int(next(lexer))
        except StopIteration:
            return

        if next(lexer) != b"(":
            raise ProtocolError('Expected "(" in FETCH response')

        fetch_data = []
        while True:
            try:
                token = next(lexer)
            except StopIteration:
                raise ProtocolError("Unexpected end of FETCH response")

            if token == b")":
                yield msg_id, fetch_data
                break

            field = token
            value = _parse_fetch_value(lexer)
            fetch_data.append((field, value))


def _parse_fetch_value(lexer: TokenSource) -> Any:
    token = next(lexer)
    if token == b"(":
        return tuple(
            _parse_fetch_value(lexer) for _ in iter(lambda: next(lexer) == b")", True)
        )
    elif isinstance(token, bytes) and token.startswith(b"{"):
        return next(lexer)
    else:
        return token


def _parse_fetch_field(field: bytes, value: Any, normalise_times: bool) -> Any:
    if field == b"INTERNALDATE":
        return parse_to_datetime(value, normalise=normalise_times)
    elif field == b"ENVELOPE":
        return Envelope.from_response(value)
    return value
