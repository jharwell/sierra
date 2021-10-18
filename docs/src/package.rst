.. _ln-package:

==================
The SIERRA Package
==================

SIERRA can be built locally into a PyPi package which you can install to provide
fully access to its functionality outside of the SIERRA repo (generally
necessary for development with SIERRA :term:`projects<Project>`), and without
modifying your :envvar:`PYTHONPATH`. Eventually, it will be deployed to PyPi,
and local installations will be unnecessary except for development of SIERRA
itself.

The SIERRA package provides the following executables:

- ``sierra-cli`` - The command line interface to SIERRA.

The SIERRA package provides the following man pages, which can be view via ``man
<name>``. Man pages are generally shorter/abridged versions of the HTML pages,
and are intended as a reference, rather than being comprehensive. Available
manpages are:

- ``sierra-cli`` - Reference for the command line interface.

- ``sierra-rendering`` - Reference for SIERRA rendering capabilities.

- ``sierra`` - All manpages rolled into one.

Installing SIERRA locally
=========================

To install SIERRA locally do the following from the SIERRA repo:

#. Build SIERRA documentation (needed for packaged manpages)::

     cd docs
     make man

#. Build SIERRA package::

     python3 -m build

#. Install SIERRA package::

     pip3 install .
