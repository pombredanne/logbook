"""Tests basic stack manipulation performance"""
from tempfile import NamedTemporaryFile

from cStringIO import StringIO

from logbook import ERROR, WARNING, FileHandler, Handler, NullHandler, StreamHandler


def run():
    f = NamedTemporaryFile()
    out = StringIO()
    with NullHandler():
        with StreamHandler(out, level=WARNING):
            with FileHandler(f.name, level=ERROR):
                for x in xrange(100):
                    list(Handler.stack_manager.iter_context_objects())
