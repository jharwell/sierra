.. _ln-sierra:

********
Synopsis
********

.. include:: description.rst

.. include:: /src/usage/cli.rst

*************
Configuration
*************

.. include:: /src/usage/environment.rst

***********
Exit Status
***********

************
Return Value
************

******
Errors
******

Generally speaking, SIERRA is very conservative, and uses lots of assert()s to
verify its internal state and the state of a given experiment at a given step of
execution before proceeding to the next step. SIERRA should rarely crash with a
cryptic interpreter error message/exception, but if it does, please report it so
I can fix it and/or create a better error message.



*****
Notes
*****

****
Bugs
****

Should be reported to :xref:`SIERRA_GITHUB`.

********
See Also
********

- :manpage:`sierra-cli`
- :manpage:`sierra-vc`
