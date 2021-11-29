.. _ln-tutorials-plugin-storage:

=============================
Creating a New Storage Plugin
=============================

For the purposes of this tutorial, I will assume you are creating a new storage
:term:`Plugin` ``infinite``, and the code for that plugin lives in
``$HOME/git/plugins/storage/infinite``.

#. Put ``$HOME/git/plugins/`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then your
   plugin can be used as ``--storage-medium=storage.infinite``.


#. Create the following directory structure within the ``infinite`` directory.

   - ``plugin.py`` - The main file which SIERRA will reference when using your
     plugin.

   That's it! You can have as many other files of whatever type you want in your
   plugin directory--they will be ignored by SIERRA.


``plugin.py`` Contents
----------------------

This file must define the following functions:

.. literalinclude:: storage_example.py
   :language: python
