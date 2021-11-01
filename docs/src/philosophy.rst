.. _ln-design-philosophy:

========================
SIERRA Design Philosophy
========================

This document outlines the main philosophy behind SIERRA's design, how it can be
used, and so forth. It really boils down to a few core ideas.

Assert Often, Fail Early
========================

If a condition arises which SIERRA can't easily handle, abort. Don't try to
recover by throwing exceptions, etc., just abort. This gives users confidence
that `if` SIERRA doesn't crash, then it is probably working properly.

Never delete things
===================

Because SIERRA is intended for academic research, and experimental data can be
hard fought, SIERRA tries to guard against accidental deletions/overwrites of
said data that users actually want to keep, but forgot to change parameters to
direct SIERRA to keep it. Therefore, we force the user to explicitly say that
deleting/overwriting is OK when it might cause irreparable damage to experiment
results (i.e., only pipeline stages 1 and 2). Overwriting is OK in later
pipeline stages since those files are built from stage 1 and 2 files.

Better Too Much Configuration Than Too Little
=============================================

SIERRA is designed to be as modular and extensible as possible (just like
ARGoS), so that it can be adapted for a wide variety of applications. When in
doubt, SIERRA exposes relevant settings as configuration (even if the average
user will never change them from their default values).

Swiss Army Pipeline
===================

SIERRAS 5-stage :ref:`Pipeline<ln-usage-pipeline>` is meant to be like a Swiss
army knife, in that you can run (mostly) arbitrary subsets of the 5 stages and
have everything work as you would expect it to, to help with tweaking
experimental design, generated graphs, etc., with minimal headaches of "Grrr I
have to wait for THAT part to run again before it will get to re-run the part I
just changed the configuration for".
