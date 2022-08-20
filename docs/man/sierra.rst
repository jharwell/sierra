======
Sierra
======

Synopsis
========

This the "main menu" of the SIERRA reference manual, which captures most, but
not all of its documentation. For the full experience, look at the online docs
at :xref:`SIERRA_DOCS`.

Components
==========

The following manpages are available:

- :manpage:`sierra-cli` - The SIERRA command line interface.

- :manpage:`sierra-usage` - How to use SIERRA (everything BUT the command line
  interface).

- :manpage:`sierra-platforms` - The target platforms that SIERRA currently
  supports (e.g., ARGoS).

- :manpage:`sierra-exec-envs` - The target execution environments that SIERRA
  currently supports (e.g., the local machine).

- :manpage:`sierra-examples` - Examples of SIERRA usage via command line
  invocations demonstrating various features.

- :manpage:`sierra-glossary` - Glossary of SIERRA terminology to make things
  easier to understand.

Errors
======

Generally speaking, SIERRA is very conservative, and uses lots of assert()s to
verify its internal state and the state of a given experiment at a given step of
execution before proceeding to the next step. SIERRA should rarely crash with a
cryptic interpreter error message/exception, but if it does, please report it so
I can fix it and/or create a better error message.

Errors should be reported to :xref:`SIERRA_GITHUB`.

Return Value
============

SIERRA will always return 0, unless it crashes with an exception or a failed
assert, in which case the return code will be non-zero.
