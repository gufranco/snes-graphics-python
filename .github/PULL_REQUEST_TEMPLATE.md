## What this changes

One or two sentences. What is different afterwards, and why it needed to be.

## How it was checked

Paste the output rather than describing it. A claim that the tests pass is not
evidence that they did.

```text
```

- [ ] `ruff format --check .` and `ruff check .` are clean
- [ ] Every test file runs, and coverage is 100% of statements and branches
- [ ] `python3 -m snesgfx.doctor` reports nothing on this machine
- [ ] `conformance/exhaustive.py` was run and every case still agrees

## If this changes what the part does

The hardware is the authority. A change to what a pixel decodes to has to name
the depth, the input bytes, and what both sides produced.

## What it does not carry

- [ ] No cartridge, no artwork, and no bytes from either
- [ ] Nothing that says where to obtain them
