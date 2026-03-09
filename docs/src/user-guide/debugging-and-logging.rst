.. SPDX-License-Identifier: MIT

.. _user-guide/debugging-and-logging:

=====================
Debugging and Logging
=====================

This page covers SIERRA's logging system, how to diagnose common failure
patterns, and techniques for isolating problems in your project or plugin
code.

.. _user-guide/debugging-and-logging/log-levels:

Log Levels
==========

SIERRA's verbosity is controlled by
:ref:`--log-level <sierra-cli---log-level>`. Levels from least to most
verbose:

``ERROR``
   Only fatal errors. Use when you want to suppress all informational
   output and check only the exit status.

``WARNING``
   Errors and warnings. SIERRA emits warnings for recoverable conditions
   such as non-existent paths on :envvar:`SIERRA_PLUGIN_PATH` or missing
   optional configuration.

``INFO``
   The default. Shows progress through pipeline stages, what plugins are
   loaded, and what experiments are being generated or run.

``DEBUG``
   Shows internal decision-making: which plugins were found and why,
   how batch criteria are parsed, what paths are being constructed. Use
   this first when something is not working as expected.

``TRACE``
   Maximum verbosity. Shows every graph being considered for generation
   and why it is being skipped or produced, every CSV file being
   processed, and every ``sys.path`` modification made by the plugin
   loader. Use this to diagnose missing graphs (stage 4) or CSV
   processing failures (stage 3).

.. code-block:: bash

   sierra-cli ... --log-level DEBUG
   sierra-cli ... --log-level TRACE

.. tip::

   For stage 4 graph problems, start with ``TRACE`` — it logs exactly
   which output CSV stem is being matched against which graph definition
   stem. A mismatch between the two is the most common cause of missing
   graphs.

.. _user-guide/debugging-and-logging/stage-failures:

Stage Failure Patterns
======================

**"Stage X crashed immediately"**
   Stage N requires stage N-1 to have completed successfully. If you
   skipped a stage or it failed silently, the next stage will crash on
   missing inputs. Check that all prior stages ran to completion before
   investigating further.

**"SIERRA hangs during stage 3 or 4"**
   The most common cause is inconsistent CSV shapes: not all experimental
   runs produced output files with the same number of rows and columns.
   SIERRA relies on uniform CSV shapes for statistics generation and does
   not validate them by default. Pass :ref:`--df-verify
   <sierra-cli---df-verify>` to catch this explicitly:

   .. code-block:: bash

      sierra-cli ... --pipeline 3 --df-verify

   If verification fails, examine which runs produced shorter outputs and
   why. For real robot experiments where minor timing differences are
   expected, :ref:`--df-homogenize <sierra-cli---df-homogenize>` can pad
   or zero-fill short columns rather than failing:

   .. code-block:: bash

      sierra-cli ... --pipeline 3 --df-homogenize pad

   Use ``pad`` only if the filled columns represent cumulative counts or
   similarly stable data. For intervallic or averaged data, padding
   produces incorrect statistics.

**"No graphs generated in stage 4"**
   SIERRA matches the stem of each output CSV against the ``src_stem``
   field in ``graphs.yaml``. If they don't match exactly, no graph is
   produced and SIERRA does not warn about it by default. Run with
   ``--log-level TRACE`` during stage 4 to see every match attempt:

   .. code-block:: bash

      sierra-cli ... --pipeline 4 --log-level TRACE

   Look for lines showing which ``src_stem`` values are being searched
   and which CSV files are present. A common cause is a trailing
   directory component in the output path that the graph definition
   doesn't account for.

**"Missing graphs for some controllers but not others"**
   Check ``controllers.yaml`` — only the graph categories listed for a
   given controller are generated. A controller that is missing a
   category will silently produce no graphs for it.

**"Stage 2 fails on HPC but works locally"** Almost always a missing environment
   variable on the compute nodes.  Check that all required variables are
   forwarded via :envvar:`PARALLEL` — see :ref:`reference/envvars`. Run with
   ``--log-level DEBUG`` to see what SIERRA is passing to GNU parallel.

.. _user-guide/debugging-and-logging/plugin-imports:

Diagnosing Plugin Import Failures
==================================

When SIERRA cannot find a plugin or project module, it reports only
"cannot locate plugin X" without showing the underlying cause. This is
because Python suppresses import errors when loading modules dynamically.
To surface the real error, import the module directly:

.. code-block:: bash

   python3 -m full.dotted.path.to.module

For example, if SIERRA cannot find ``myproject.generators.scenario``:

.. code-block:: bash

   python3 -m myproject.generators.scenario

This runs the module as a script and prints any ``ImportError``,
``ModuleNotFoundError``, or syntax error that would otherwise be
swallowed. Common causes:

- A transitive dependency is missing (``pip install`` it)
- A relative import in the module doesn't resolve (check ``__init__.py``
  exists at each package level)
- A C extension library is not on :envvar:`LD_LIBRARY_PATH`
- :envvar:`PYTHONPATH` or :envvar:`SIERRA_PLUGIN_PATH` is not set
  correctly for the current shell

To verify the plugin search path SIERRA is actually using, run with
``--log-level DEBUG`` and look for lines beginning with
``Searching for plugins in``:

.. code-block:: bash

   sierra-cli ... --log-level DEBUG --pipeline 1 2>&1 | grep "plugins in\|sys.path\|Updated"

.. _user-guide/debugging-and-logging/minimal-batch:

Isolating Problems with a Minimal Batch
========================================

Most problems are faster to diagnose with the smallest possible batch.
Use ``builtin.MonteCarlo.C1`` to produce a single experiment and
``--pipeline 1`` to exercise only stage 1:

.. code-block:: bash

   sierra-cli                                   \
     --project        myproject                 \
     --engine         engine.argos              \
     --expdef-template exp/template.argos       \
     --batch-criteria builtin.MonteCarlo.C1     \
     --scenario       myScenario.10x10x1        \
     --controller     myCategory.myController   \
     --pipeline 1                               \
     --log-level DEBUG

Stage 1 exercises plugin loading, project discovery, batch criteria
parsing, and experiment generation without running any simulations. If
stage 1 passes, the problem is in stage 2 or later. Add stages
incrementally until the failure appears.

Once stage 1 passes with a single experiment, add ``--pipeline 2`` with
a short experiment duration (via ``--exp-setup`` if your engine supports
it) to validate stage 2 before committing to a full batch run.

This same invocation doubles as an environment setup check. If stage 1
passes, :envvar:`SIERRA_PLUGIN_PATH`, :envvar:`PYTHONPATH`, and plugin
discovery are all configured correctly for stages 2–5.
