"""Statement formats. Each bank module names its header, bank and account, and reads its rows."""

from tally.formats import birchwood, fernhill

FORMATS = (birchwood, fernhill)


class UnknownFormat(ValueError):
    pass


def detect(header):
    """Return the format whose header matches the CSV header exactly."""
    names = [name.strip() for name in header]
    for fmt in FORMATS:
        if names == fmt.HEADER:
            return fmt
    raise UnknownFormat("unrecognized statement header: %s" % ",".join(names))
