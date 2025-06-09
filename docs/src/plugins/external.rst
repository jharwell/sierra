..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/external:

======================
Using External Plugins
======================

When using a plugin which you have created and placed on
:envvar:`SIERRA_PLUGIN_PATH`, there are some important aspects to be aware of,
detailed below.

Recursive Plugin Search
-----------------------

To support dynamic plugins which can be defined anywhere, each directory on the
plugin path is searched recursively. Any file/directory matching a :ref:`schema
<plugins/devguide/schemas>` that SIERRA supports will be loaded.  For example, if you
have a plugin ``$HOME/git/organization/plugins/myplugin``, you can make it
accessible in SIERRA in a number of different ways:

- Put ``$HOME/git`` on ``SIERRA_PLUGIN_PATH`` -> your plugin will be accessible
  as ``plugins.myplugin`` on the cmdline.

- Put ``$HOME/git/organization`` on ``SIERRA_PLUGIN_PATH`` -> your plugin will
  be accessible as ``plugins.myplugin`` on the cmdline.

- Put ``$HOME/git/organization/plugins`` on ``SIERRA_PLUGIN_PATH`` -> your
  plugin will be accessible as ``plugins.myplugin`` on the cmdline.

You may wonder "Why use a plugin path at all? Why not just recursively search
from /" ? There are a couple reasons:

- SIERRA's schema for plugins is not guaranteed to be unique now
  and forever in all cases, for all systems, etc.

- Recursively searching from / can take *forever* on some systems making SIERRA
  mostly unusable.

- Only putting some subdirs under a common prefix on ``SIERRA_PLUGIN_PATH`` is a
  good way to exclude certain plugins from loading; this is useful if you have
  multiple plugins with the same name, or have a plugin which isn't working
  currently and you want to effectively disable it from loading to continue on
  with your work.

Modifications to ``sys.path``
-----------------------------

Once a plugin is loaded, the *parent* directory of the directory it which it was
found is added to ``sys.path``. Referring to the example above, that would be
``$HOME/git/organization``. Thus if you need to import modules among the
different files in your plugin, *all imports must be relative to the parent
directory of the plugin*. So::

  import plugins.myplugin              # valid
  import organization.plugins.myplugin # invalid
  import myplugin                      # invalid


Entries earlier in ``sys.path`` take precedence over those which are later, and
plugins external to SIERRA have their modifications earlier in ``sys.path``, you
cannot generally have the same plugin directory hierarchy as SIERRA, because the
package for e.g., ``engine`` will be picked up in your project, and thus
something like ``import engine.argos`` will fail, because that isn't defined in
your module. Concretely, if you have::

  $HOME/myproject/engine/simengine/
    - plugin.py
    - __init__.py

and ``$HOME/`` is on ``SIERRA_PLUGIN_PATH``, then SIERRA will fail to start with
a rather cryptic error. If you instead have::

    $HOME/myproject/plugins/simengine/
    - plugin.py
    - __init__.py


Then your ``simengine`` plugin is accessible as ``plugins.simengine``.

If you really want to do this, you would need to do something
like ``from sierra.core.engine import`` in ``__init__.py`` in the above example,
but this isn't recommended, as it will probably have all sorts of subtle
consequences.
