# Open questions

What this project does not know for certain, and what it would take to find out.

The list is short, and shorter than any other member's, for a reason worth
stating plainly: these are layouts rather than parts. A layout is right or wrong,
several of the input spaces here are small enough to walk from end to end, and
where a space is walked there is no case left to be uncertain about.

What that walking does **not** establish is the one thing worth being careful
about, and it has its own entry below.

Every entry is also in
[`conformance/divergences.json`](conformance/divergences.json) with its status
and severity, so a program can read what a person reads here.

## Why an exhaustive walk cannot close these

A complete round trip over a whole space is strong evidence that a decoder and an
encoder agree with each other. It is not evidence about the hardware: a decoder
and an encoder that were wrong in exactly opposite ways would pass every one of
the 165,248 cases.

What closes that gap is
[`conformance/hardware.test.py`](conformance/hardware.test.py), which holds each
layout against the figures Nintendo printed in Appendix A of Book 1. Before it
existed, the badge counted 165,248 cases of self-consistency and said nothing
else.

## What would settle almost all of them

One more page of the same manual. Both entries below are figures that Appendix A
either prints on a page not yet read or does not print at all.

## Where a figure follows by arithmetic rather than being printed

### The width of a colour channel.

**The document says.** That a colour is two bytes, and that the register ordering
its fields runs blue, green, red. It does not print the channel width.

Source: Nintendo of America Inc., *SNES Development Manual, Book 1*, Appendix A.

**What this project follows.** Five bits per channel, with the top bit of the
word unused.

**Why.** Fifteen bits over three channels gives five each. That follows from the
two figures rather than being one of them, so it is named here rather than sitting
in [`conformance/hardware.json`](conformance/hardware.json) as though Nintendo
had written it down.

**What would settle or reopen it.** The CGRAM figure at page A-17, or any passage
giving the channel width outright.

### What the hardware does with a character code above the range the field holds.

**The document says.** Nothing, and it has no reason to: the field cannot hold
one.

**What this project follows.** It refuses the value rather than masking it,
because masking would store something the caller did not ask for and read it back
as though they had.

**What would settle or reopen it.** Nothing available. The question is about a
value that cannot reach the hardware through this layout, so a measurement would
have to reach it some other way.

## Where the question is a scope boundary, not an unknown

### When the display reads any of this.

**The document says.** Layouts in memory.

**What this project follows.** Neither. This package converts between a layout
and pixels and asks nothing about time.

**Why.** When the display reads one of these, and what happens if the console
writes while it does, is a different question belonging to whatever models the
display. A converter that also answered it would be two models in one package,
and the second would have nothing behind it.

**What would settle or reopen it.** Nothing. This is a boundary rather than a
gap, and it is listed so a reader does not mistake the first for the second.

## What was open and is now measured

**Whether the published grouping is the one cartridges actually use.** It is, by
a margin nobody has to take on trust. Every other check here proves the code
agrees with a record, with a second reading of the same manual, and with itself
over the whole input space, and none of that can tell a correct reading from a
plausible one: a decoder that misread the manual agrees with a record written
from the same misreading.

[`conformance/against_cartridges.py`](conformance/against_cartridges.py) reads
real cartridge bytes three ways and asks which reading finds the most structure,
on the grounds that a picture read with the right grouping has neighbours that
match and read with the wrong one does not. The two alternatives are not
strawmen: contiguous planes is how other consoles of the period stored the same
kind of tile, and two pixels to a byte is the obvious way to hold sixteen
colours.

| Reading | Regions won |
| --- | --- |
| the published grouping | 6,178 of 11,765, 52.5% |
| contiguous planes | 3,735, 31.7% |
| two pixels to a byte | 1,852, 15.7% |
| a reading with nothing in it | 33.3% |

Regions are picked by where they sit rather than by what is in them, and all
three readings see the same regions, so the reading under test gets no help from
selection. The statistic counts whether neighbouring pixels are equal and never
looks at which colour they are, so a grouping difference that only renames
colours cannot move it. That is deliberate, and it is why the first version of
this check reported nothing: swapping the plane pairs scored identically, which
is correct, because that difference is not one anybody can see.

The images are not carried. 300 of the 7,578 on this machine were read, drawn by
a fixed seed so another machine with the same library reads the same 300.

## What is not in question

So the boundary is visible rather than implied:

- **Every two bit tile that can exist.** 65,536 cases, round tripped both ways.
- **Every map entry word.** 65,536 cases, decoded into fields and re-encoded.
- **Every colour the hardware can name.** 32,768 cases, widened to bytes and
  narrowed back. A shift-based conversion fails this and repeating the value's
  own high bits into the gap passes it, which is why the widening is written the
  way it is.
- **Every plane of every depth against every one of the sixty four pixels.** 896
  cases. This is what stands in for walking a four bit tile, which has more
  states than is worth counting, and it is the property that actually matters: a
  plane must reach its own bit of every pixel and no other bit of anything.
- **Every sprite's two bits in the second table.** 512 cases, without disturbing
  its neighbours.
- **That each layout matches the figure Nintendo printed.** Held by
  [`conformance/hardware.test.py`](conformance/hardware.test.py), which is what
  separates a round trip from a claim about the hardware.
- **That each walk can fail.** The tests break each format deliberately and
  confirm the walk catches it.

## What is deliberately not modelled

Absent rather than unknown, and absent on purpose:

- **Any image file.** Turning pixels into a PNG is a different problem with
  existing answers, and pulling one in would make a package with no dependencies
  into one with several.
- **Six bits per pixel.** Several tools list it. No Super Nintendo background
  mode has it.
- **Mathematically correct Mode 7 products.** The multiplier truncates before the
  terms are added, so a matrix entry small enough that its product falls under
  sixty four contributes nothing at all: a very slow rotation stays exactly still
  and then jumps. A model more accurate than the hardware is wrong, and software
  tuned on hardware looks broken on one.
- **Anything with a clock.** These are layouts. There is no part here to drive.
