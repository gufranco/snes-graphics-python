"""Everything this package raises, in one place.

One module so a caller can see the whole set at once, and so `except` has
somewhere to import from. It imports nothing from the rest of the package, which
is what keeps it from ever closing a cycle: everything here raises, so everything
here imports this, and an import running the other way would make the order
modules happen to load in decide whether the package works at all.

This module exists because the alternative was here and working. Four modules
each defined their own `Truncated` and four each defined their own `OutOfRange`.
Every one of the eight worked, every one was tested, and `except tiles.Truncated`
written against a tile sailed straight past the one a palette raised, because two
classes under one name are two different objects that compare equal only by name.
Nothing failed, which is what made it worth fixing.
"""

from __future__ import annotations


class Truncated(Exception):
    """The data is not a whole number of whatever it is being read as.

    A layout has a unit, and a buffer that holds part of one has no reading. It
    is refused rather than padded, because padding invents bytes and reading a
    short buffer as though it were long produces a picture that is subtly wrong
    rather than obviously absent.

    One class for every layout here, deliberately. A caller decoding a sheet does
    not want to know which of six modules noticed the length was wrong.
    """


class OutOfRange(Exception):
    """A value does not fit the field it is being written into.

    Fields here are narrow: a ten bit tile number, a three bit palette block, a
    five bit colour channel. Masking a value that overflows would store something
    the caller did not ask for and read it back as though they had.
    """


class UnknownDepth(Exception):
    """No tile depth by that name exists on this hardware.

    Named separately from `OutOfRange` because it is a different mistake. A depth
    is chosen from a fixed set rather than checked against a bound, and the one
    people reach for that does not exist is six bits per pixel, which several
    tools offer and the hardware does not have.
    """


class UnknownFormat(Exception):
    """No layout goes by that name, under any spelling this package accepts.

    The message names the layouts that would have worked, because a refusal that
    does not costs the caller a search through the source.
    """
