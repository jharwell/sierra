.. _ln-tutorials-plugin-hpc:

=========================
Creating a New HPC Plugin
=========================

For the purposes of this tutorial, I will assume you are creating a new HPC
:term:`Plugin` ``HAL``, and the code for that plugin lives in
``$HOME/git/plugins/hpc/HAL``.

#. Put ``$HOME/git/plugins/hpc/HAL`` on your
   :envvar:`SIERRA_PLUGIN_PATH`. Then your plugin can be used as
   ``--hpc-env=hpc.HAL``.

#. Create the following directory structure within the ``HAL`` directory.

   - ``main.py`` - The main file which SIERRA will reference when using your
     plugin.

   That's it! You can have as many other files of whatever type you want in your
   plugin directory--they will be ignored by SIERRA.


``main.py`` Contents
--------------------

This file must define the following functions:

.. literalinclude:: hpc_example.py
   :language: python
