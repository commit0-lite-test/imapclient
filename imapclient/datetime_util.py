import re
from datetime import datetime
from email.utils import parsedate_tz
from .fixed_offset import FixedOffset

_SHORT_MONTHS = " Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ")


def parse_to_datetime(timestamp: bytes, normalise: bool = True) -> datetime:
    """Convert an IMAP datetime string to a datetime.

    If normalise is True (the default), then the returned datetime
    will be timezone-naive but adjusted to the local time.

    If normalise is False, then the returned datetime will be
    unadjusted but will contain timezone information as per the input.
    """
    timestamp_str = timestamp.decode("ascii")
    parsed = parsedate_tz(timestamp_str)
    if parsed is None:
        raise ValueError(f"Could not parse datetime string: {timestamp_str}")

    dt = datetime(*parsed[:6])
    offset_seconds = parsed[-1]

    if offset_seconds is not None:
        dt = dt.replace(tzinfo=FixedOffset(offset_seconds // 60))

    if normalise:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def datetime_to_INTERNALDATE(dt: datetime) -> str:
    """Convert a datetime instance to a IMAP INTERNALDATE string.

    If timezone information is missing the current system
    timezone is used.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=FixedOffset.for_system())

    return dt.strftime("%d-%b-%Y %H:%M:%S %z")


_rfc822_dotted_time = re.compile(
    "\\w+, ?\\d{1,2} \\w+ \\d\\d(\\d\\d)? \\d\\d?\\.\\d\\d?\\.\\d\\d?.*"
)


def format_criteria_date(dt: datetime) -> bytes:
    """Format a date or datetime instance for use in IMAP search criteria."""
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt.strftime("%d-%b-%Y").encode("ascii")
