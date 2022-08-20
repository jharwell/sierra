.. _ln-sierra-tutorials-plugin-storage:

=============================
Creating a New Storage Plugin
=============================

For the purposes of this tutorial, I will assume you are creating a new storage
:term:`Plugin` ``infinite``, and the code for that plugin lives in
``$HOME/git/plugins/storage/infinite``.

Create the Code
===============

#. Create the following filesystem structure in
   ``$HOME/git/plugins/storage/infinite``:

   .. tabs::

      .. tab::  ``plugin.py``

         .. include:: plugin.rst

Connect to SIERRA
=================

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--exec-env=storage.infinite``.

.. NOTE:: Storage plugin names have the same constraints as python package names
   (e.g., no dots).
