.. _ln-exp-requirements:


===================================
SIERRA Requirements for Experiments
===================================

SIERRA makes a few assumptions about how :term:`Experimental Runs<Experimental
Run>` are defined (i.e., limitations), depending on the :term:`Platform`
selected.

SIERRA Requirements for ARGoS C++ Libraries
===========================================

#. All swarms are homogeneous (i.e., only contain 1 type of robot). While SIERRA
   does not currently support  multiple types of robots, adding support for
   doing so would not be difficult.

#. The distribution method via ``<distribute>`` in the ``.argos`` file is the
   same for all robots, and therefore only one such tag exists (not checked).
