.. SIERRA documentation master file, created by
   sphinx-quickstart on Sat Oct 12 17:39:54 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

How To Use SIERRA
=================

The following steps outline things to do to get up and running with SIERRA, once
you have completed the setup steps (either :ref:`ln-msi-setup` or
:ref:`ln-nonmsi-setup`).

#. Decide what variable you are interested in investigating by consulting
   :ref:`ln-batch-criteria`.

#. Determine how to invoke SIERRA. At a minimum you need to tell it the
   following:

   - What template input file to use: ``--template-input-file``.

   - How many copies of each simulation to run per experiment: ``--n-sims``.

   - How many threads to use per simulation: ``--n-threads``.

   - Where it is running/how to run experiments: ``--exec-method``.

   - How long simulations should be: ``--time-setup``.

   - What controller to run: ``--controller``.

   - What what block distribution type to use, and how large the arena should be:
     ``--scenario``.

   - What you are investigating; that is, what variable are you interested in
     varying: ``--batch-criteria``.

   If you try to invoke SIERRA with an (obviously) incorrect combination of
   command line options, it will refuse to do anything. For less obviously
   incorrect combinations, it will (hopefull) stop when an assert fails before
   doing anything substantial.

   Full documentation of all command line options it accepts is in
   :ref:`ln-cli`, and there are many useful options that SIERRA accepts, so
   skimming the CLI docs is **very** worthwhile.

#. Learn SIERRA's runtime :ref:`ln-runtime-exp-tree`. When running, SIERRA will
   create a (rather) large directory structure for you, which can be mystifying
   at first. Reading the docs is worthwhile to understand what the structure
   means, and to gain intuition into where to look for things inputs/outputs
   etc. without having to search exhaustively through the filesystem.

#. If running SIERRA on MSI, learn how to submit jobs by reading
   :ref:`ln-msi-runtime`.

General Usage Tips
------------------

- The best way to figure out what SIERRA can do is by reading the :ref:`ln-cli`
  docs. Every option is very well documented. The second best way is to look at
  the scripts under ``scripts/``.

- There are 5 pipeline stages, though only the first 4 will run automatically.

- If you run stages individually, then before stage X will probably run
  without crashing, you need to run stage X-1.

- If you are using a ``quad_source`` block distribution, the arena should be at
  least 16x16 (smaller arenas don't leave enough space for caches and often
  cause segfaults).

- When using multiple physics engines, always make sure that ``# engines / arena
  dimension`` (X **AND** Y dimensions) is always a rational number. That is,

  - 24 engines in a ``12x12`` arena will be fine, because ``12/24=0.5``, which
    can be represented reasonably well in floating point.

  - 24 engines in a ``16x16`` arena will not be fine, because
    ``16/24=0.666667``, which will very likely result in rounding errors and
    ARGoS being unable to initialize the space because it can't place arena
    walls.

  This is enforced by SIERRA.

- For ``SS,DS`` distributions a rectangular 2x1 arena is required. That is, an
  arena where the X dimension is twice the Y dimension. If you try to run with
  anything else, you will get an error.

- For ``QS,PL,RN`` distributions a square arena is required (if you try to run
  with anything else, you will get an error).

.. toctree::
   :maxdepth: 2
   :caption: Full Usage Docs:

   batch_criteria.rst
   cli.rst
   directories.rst
   msi.rst
