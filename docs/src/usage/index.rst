=================
How To Use SIERRA
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents

   batch_criteria.rst
   variables.rst
   pipeline.rst
   cli.rst
   run_time_tree.rst
   rendering.rst
   examples.rst
   subprograms.rst
   environment.rst

General Usage Tips
------------------

- The best ways to figure out what SIERRA can do are:

  #. Reading the :ref:`ln-batch-criteria` docs.

  #. Reading the :ref:`ln-usage-cli` docs. Every option is very well documented.

  #. Look at scripts under ``scripts/``, which are scripts I've used before on
     MSI (they might no longer work, but they do give you some idea of how to
     invoke SIERRA).

- If you are running the :xref:`FORDYCA` project and using a ``quad_source``
  block distribution, the arena should be at least 16x16 (smaller arenas don't
  leave enough space for caches and often cause segfaults).

- For ``SS,DS`` distributions a rectangular 2x1 arena is required. That is, an
  arena where the X dimension is twice the Y dimension. If you try to run with
  anything else, you will get an error.

- For ``QS,PL,RN`` distributions a square arena is required (if you try to run
  with anything else, you will get an error).
