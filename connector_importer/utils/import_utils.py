# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import csv
import io
import time

from ..log import logger

try:
    from chardet.universaldetector import UniversalDetector
except ImportError:
    import logging

    _logger = logging.getLogger(__name__)
    _logger.debug("`chardet` lib is missing")


def get_encoding(data):
    """Try to get encoding incrementally.

    See http://chardet.readthedocs.org/en/latest/usage.html#example-detecting-encoding-incrementally  # noqa
    """
    start = time.time()
    msg = "detecting file encoding..."
    logger.info(msg)
    file_like = io.BytesIO(data)
    detector = UniversalDetector()
    for _i, line in enumerate(file_like):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    msg = "encoding found in %s sec" % str(time.time() - start)
    msg += str(detector.result)
    logger.info(msg)
    return detector.result


def csv_content_to_file(data, encoding=None):
    """Odoo binary fields spit out b64 data."""
    # guess encoding via chardet (LOVE IT! :))
    if not encoding:
        encoding_info = get_encoding(data)
        encoding = encoding_info["encoding"]
    if encoding is None or encoding != "utf-8":
        try:
            data_str = data.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            # dirty fallback in case
            # we don't spot the right encoding above
            for enc in ("utf-16le", "latin-1", "ascii"):
                try:
                    data_str = data.decode(enc)
                    break
                except UnicodeDecodeError:
                    data_str = data
        data_str = data_str.encode("utf-8")
    else:
        data_str = data
    return data_str


def guess_csv_metadata(filecontent):
    # we don't care about acuracy but we don't to get an unicode error
    # when converting to str
    encoding = get_encoding(filecontent)
    with io.StringIO(str(filecontent, encoding["encoding"])) as ff:
        try:
            dialect = csv.Sniffer().sniff(ff.readline(), "\t,;")
            ff.seek(0)
            meta = {"delimiter": dialect.delimiter, "quotechar": dialect.quotechar}
        except BaseException:
            meta = {}
        return meta


def read_path(path):
    with open(path, "r") as thefile:
        return thefile.read()


class CSVReader(object):
    """Advanced CSV reader."""

    def __init__(
        self,
        filepath=None,
        filedata=None,
        delimiter="|",
        quotechar='"',
        encoding=None,
        fieldnames=None,
        rows_from_to=None,
    ):
        assert filedata or filepath, "Provide a file path or some file data!"
        if filepath:
            filedata = read_path(filepath)
        self.bdata = csv_content_to_file(filedata, encoding)
        self.data = str(self.bdata, "utf-8")
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.fieldnames = fieldnames
        self.rows_from_to = rows_from_to or ""

    def read_lines(self):
        """Yields lines and add info to them (like line nr)."""
        lines = self.data.splitlines()
        if ":" in self.rows_from_to:
            header = lines[0]
            lines = lines[1:]
            _from, _to = self.rows_from_to.split(":")
            lines = [
                header,
            ] + lines[int(_from or 0) : int(_to or len(lines) + 1)]
        reader = csv.DictReader(
            lines,
            delimiter=str(self.delimiter),
            quotechar=str(self.quotechar),
            fieldnames=self.fieldnames,
        )
        for line in reader:
            line["_line_nr"] = reader.line_num
            yield line


def gen_chunks(iterable, chunksize=10):
    """Chunk generator.

    Take an iterable and yield `chunksize` sized slices.
    """
    chunk = []
    for i, line in enumerate(iterable):
        if i % chunksize == 0 and i > 0:
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield chunk
