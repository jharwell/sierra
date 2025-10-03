..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/collate:

===============================
Intra-Experiment Data Collation
===============================

Motivation
==========

When generating products, it is often necessary to perform some sort of
non-statistical mathematical analysis on the results. These calculations
*cannot* be done on the intra-experiment :term:`Processed Output Data` files,
because any calculated statistical distributions from them will be invalid; this
can be thought of as an average of sums is not the same as a sum of averages.
To support such use cases, SIERRA can make the necessary parts of the per-run
:term:`Raw Output Data` files available in stage 3 for doing such calculations
via :term:`Data Collation`. Of course, like all things in SIERRA, if you don't
need this functionality, you can turn it off by deselecting the plugin.

This process in stage 3 can be visualized as follows for a single
:term:`Experiment`:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateBorderThickness 8

   state "User\nSpecification" as user #lightcoral

   state "run 0" as run0 {
      state "file0" as file00 #skyblue {
         state "col0" as col000 #darkturquoise
         state "col1" as col001 #limegreen
      }
      state "file 1" as file01  #skyblue {
         state "colA" as col010 #green
         state "colB" as col011 #lightseagreen
      }
      state "..." as file0x #skyblue
   }
   state "run 1" as run1 {
      state "file0" as file10 #skyblue {
         state "col0" as col100 #darkturquoise
         state "col1" as col101 #limegreen
      }
      state "file 1" as file11  #skyblue {
         state "colA" as col110 #green
         state "colB" as col111 #lightseagreen
      }
      state "..." as file1x #skyblue
   }
   state "..." as runx #skyblue

   state "run j" as runj {
      state "file0" as filej0 #skyblue {
         state "col0" as colj00 #darkturquoise
         state "col1" as colj01 #limegreen
      }
      state "file1" as filej1  #skyblue {
         state "colA" as colj10 #green
         state "colB" as colj11 #lightseagreen
      }
      state "..." as filejx #skyblue
   }

   state "Processed outputs" as inter {
      state "col0 file" as filep0 #darkturquoise {
         state "run 0" as colp00
         state "run 1" as colp01
         state "..." as colp0x
         state "run j" as colp0j
      }
      state "col1 file" as filep1 #limegreen {
         state "run 0" as colp10
         state "run 1" as colp11
         state "..." as colp1x
         state "run j" as colp1j
      }
      state "colA file" as filep2 #green {
         state "run 0" as colp20
         state "run 1" as colp21
         state "..." as colp2x
         state "run j" as colp2j
      }
      state "colB file" as filep3 #lightseagreen {
         state "run 0" as colp30
         state "run 1" as colp31
         state "..." as colp3x
         state "run j" as colp3j
      }
   }

   filep0 -[hidden]r-> filep1
   filep2 -[hidden]r-> filep3
   filep0 -[hidden]d-> filep2
   filep1 -[hidden]d-> filep3

   user --> run0
   user --> run1
   user --> runx
   user --> runj

   run0 --> inter
   run1 --> inter
   runx --> inter
   runj --> inter


Here, the user has specified that the ``col{0,1}`` in ``file0`` produced by all
experimental runs should be combined into a single file. Thus the
:term:`Collated Output Data` file generated from that specification will have
:math:`j` columns, one per run. Similarly for ``col{A,B}`` in ``file1``. This is
collation *within* in an experiment (intra-experiment). Collation *across*
experiments (if enabled/configured) is done during stage 4, and is handled by a
different plugin.

Usage
=====

This plugin can be selected by adding ``proc.collate`` to the list passed to
``--proc``.  Configuration for this plugin consists of *what* data to collate,
and some tweaks for *how* that data should be collated.

This plugin does not require additional plugins to be active when it is run.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/proc/collate/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

Configuration
-------------

Controls *what* to collate. Collated data is usually "interesting" in some way;
e.g., related to system performance. Configuration lives in a ``collate.yaml``
file; all fields are required unless otherwise specified.

.. code-block:: YAML

   # Contains a list of config items for intra-experiment collation (i.e.,
   # collation at the level of experimental runs).
   intra-exp:

     # Each config item has 'file' and 'cols' fields. 'file' specifies a
     # filepath, relative to the output directory for each experimental run,
     # containing the data columns of interest. 'cols' specifies the columns of
     # interest.
     - file: foo/bar
       cols:
         - col1
         - col2
