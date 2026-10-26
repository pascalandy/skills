"""JSON encoding for API responses.

Keys are sorted so the same result always encodes to the same bytes, which
keeps cached responses and response diffs stable. Floats are rounded for
display.
"""

import json

FLOAT_DIGITS = 2


def rounded(value):
    if isinstance(value, float):
        return round(value, FLOAT_DIGITS)
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [rounded(item) for item in value]
    return value


def dumps(payload):
    return json.dumps(rounded(payload), sort_keys=True, ensure_ascii=False)
