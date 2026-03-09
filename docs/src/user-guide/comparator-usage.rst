..
   Copyright 2026 John Harwell, All rights reserved.

.. SPDX-License-Identifier: MIT

.. _user-guide/comparator-usage:

=================
Comparing Results
=================

Stage 5 overlays results from multiple batch experiments onto shared graphs.
It requires stage 4 to have completed successfully for every batch experiment
being compared. For available options and example invocations, see
:ref:`reference/cli` and :ref:`user-guide/examples`.

.. _user-guide/comparator-usage/prerequisites:

Prerequisites
=============

Stage 5 reads the inter-experiment collated CSV files produced by stage 4.
Every batch experiment in the comparison must have a populated
``stat_interexp`` directory; SIERRA warns and skips any that do not, but does
not abort. If stage 5 produces fewer graphs than expected, missing
``stat_interexp`` directories are the most common cause.

For two experiments to be comparable they must have been run with the same
batch criteria. SIERRA checks this pairwise and issues warnings for
mismatches, but continues. Graphs generated from mismatched criteria will
have incorrect axis labels.

.. _user-guide/comparator-usage/outputs:

Output Location
===============

Stage 5 writes graphs and intermediate CSVs into the project root
(``<sierra-root>/<project>/``), in directories named after the compared
things:

- Controller comparisons: ``<c1>+<c2>+...-cc-graphs/`` and
  ``<c1>+<c2>+...-cc-csvs/``
- Scenario comparisons: ``<s1>+<s2>+...-sc-graphs/`` and
  ``<s1>+<s2>+...-sc-csvs/``

Because the directory name encodes the compared set, re-running stage 5 with
a different ``--things`` list writes to a different directory and does not
overwrite previous results.
