import sys
from munch import Munch, munchify
from functools import total_ordering


@total_ordering
class ComparableMunch(Munch):

    def __eq__(self, other):
        return id(self) == id(other)

    def __lt__(self, other):
        return id(self) < id(other)


def custom_munchify(data, factory=ComparableMunch):
    return munchify(data, factory)


def munchify_factory():
    if sys.version_info >= (3, 0):
        return custom_munchify
    else:
        return munchify
