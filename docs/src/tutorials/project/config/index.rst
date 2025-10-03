.. _tutorials/project/config:

==========================
Project YAML Configuration
==========================

There are three main configuration files that you may define so that SIERRA
knows how to interact with your project. Some are required, some are
optional. The more of them you define, the more SIERRA will be able to do
automatically for you!

.. tabs::

   .. tab:: ``config/main.yaml``

      .. include:: main.rst


   .. tab:: ``config/collate.yaml``

      See :ref:`plugins/proc/collate`.

   .. tab:: ``config/controllers.yaml``

      .. include:: controllers.rst

.. NOTE:: There is not currently a ``scenarios.yaml`` complement to the
          ``controllers.yaml``. This is by design. The specified ``--scenario``
          more often than not has a detailed/complex set of changes to make to
          an ``--expdef-template`` which is not well-suited to a declarative
          paradigm, whereas the specified ``--controller`` more often than not
          has a simple set of changes to make to an ``--expdef-template``. Put
          another way, ``--controller`` semantics are (usually) much simpler
          than ``--scenario`` semantics, and thus instance-specific changes are
          implemented declaratively.

          This may be revisited in a future version of SIERRA.
