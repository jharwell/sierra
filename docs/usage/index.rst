.. Sierra documentation master file, created by
   sphinx-quickstart on Sat Oct 12 17:39:54 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Usage
=====

.. toctree::
   :maxdepth: 2
   :caption: Contents:

  msi.rst
  directories.rst
  cli.rst
  batch_criteria.rst
  controllers.rst

General Usage
-------------

When using sierra, you need to tell it the following (at a minimum):

- What template input file to use: ``--template-config-file``.

- How many copies of each simulation to run per experiment: ``--n-sims``.

- Where it is running/how to run experiments: ``--exec-method``.

- How long simulations should be: ``--time-setup``.

- What controller to run: ``--controller``.

- What what block distribution type to use, and how large the arena should be:
  ``--scenario``.

- What you are investigating; that is, what variable are you interested in
  varying: ``--batch-criteria``.

Head over to the :ref:`ln-cli` docs to see what these options mean.

Usage Tips
----------

- The best way to figure out what sierra can do is by reading the :ref:`ln-cli`
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
  ``16/24=0.666667``, which will very likely result in rounding errors and ARGoS
  being unable to initialize the space because it can't place arena walls.
