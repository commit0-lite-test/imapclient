import binascii
from typing import Union


def encode(s: Union[str, bytes]) -> bytes:
    """Encode a folder name using IMAP modified UTF-7 encoding.

    Input is unicode; output is bytes (Python 3) or str (Python 2). If
    non-unicode input is provided, the input is returned unchanged.
    """
    if isinstance(s, bytes):
        return s
    if not isinstance(s, str):
        raise ValueError("Input must be str or bytes")

    result = bytearray()
    utf16 = s.encode("utf-16be")
    for i in range(0, len(utf16), 2):
        char = (utf16[i] << 8) | utf16[i + 1]
        if 0x20 <= char <= 0x7E and char != AMPERSAND_ORD:
            result.extend(chr(char).encode("ascii"))
        else:
            result.append(AMPERSAND_ORD)
            start = i
            while i < len(utf16):
                char = (utf16[i] << 8) | utf16[i + 1]
                if 0x20 <= char <= 0x7E and char != AMPERSAND_ORD:
                    break
                i += 2
            result.extend(binascii.b2a_base64(utf16[start:i]).rstrip(b"\n"))
            result.append(DASH_ORD)
            i -= 2
    return bytes(result)


AMPERSAND_ORD = ord("&")
DASH_ORD = ord("-")


def decode(s: Union[bytes, str]) -> str:
    """Decode a folder name from IMAP modified UTF-7 encoding to unicode.

    Input is bytes (Python 3) or str (Python 2); output is always
    unicode. If non-bytes/str input is provided, the input is returned
    unchanged.
    """
    if isinstance(s, str):
        s = s.encode("ascii")
    if not isinstance(s, bytes):
        raise ValueError("Input must be str or bytes")

    result = []
    i = 0
    while i < len(s):
        if s[i] == AMPERSAND_ORD:
            start = i + 1
            end = s.find(b"-", start)
            if end == -1:
                end = len(s)
            if start == end:
                result.append("&")
            else:
                encoded = s[start:end]
                try:
                    decoded = binascii.a2b_base64(encoded + b"===")
                    result.append(decoded.decode("utf-16be"))
                except (binascii.Error, UnicodeDecodeError):
                    result.append("&" + encoded.decode("ascii") + "-")
            i = end + 1
        else:
            result.append(chr(s[i]))
            i += 1
    return "".join(result)
