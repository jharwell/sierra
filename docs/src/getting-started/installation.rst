.. _getting-started/installation:

=================
Installing SIERRA
=================

This page covers everything you need before running ``sierra-cli`` for the
first time.

.. note::

   **Python 3.9–3.12 is required.** Older versions are not supported; as they
   reach end-of-life, support is dropped so SIERRA can use newer language
   features. Newer versions beyond 3.12 may work but are not yet tested.

Prerequisites
=============

SIERRA depends on a small set of OS-level utilities. Install them before
running ``pip install``.

.. tabs::

   .. group-tab:: Ubuntu / Debian

      .. code-block:: bash

         sudo apt install parallel psmisc

   .. group-tab:: Fedora / RHEL

      .. code-block:: bash

         sudo dnf install parallel psmisc

   .. group-tab:: macOS

      .. code-block:: bash

         brew install parallel

.. IMPORTANT::

   SIERRA will not work correctly if these packages are missing. It may start
   and appear to run, but certain features will fail silently or with cryptic
   errors. Install them before proceeding.

If you are on a different Linux distribution, install the equivalents of
``parallel`` and ``psmisc`` from your package manager.

.. note::

   The prerequisites above cover the SIERRA core only. Many
   :ref:`plugins <plugins>` have additional OS-level requirements, documented
   on their respective pages.

Installing SIERRA
=================

.. code-block:: bash

   pip3 install sierra-research

This installs the ``sierra-cli`` executable and all Python dependencies. After
installation, verify it works:

.. code-block:: bash

   sierra-cli --help

Man pages are also installed and can be browsed offline via ``man sierra-cli``,
``man sierra-usage``, ``man sierra-plugins``, ``man sierra-examples``, and
``man sierra-glossary``. See :doc:`../reference/cli-reference` for the full CLI
reference in these docs.

.. dropdown:: ROS users: additional setup required
   :icon: info

   .. _packages/rosbridge:

   When using a :term:`ROS1`-based :term:`Engine`, SIERRA requires a companion
   ROS package that provides run-time simulation management and project support.

   Source and full setup instructions:
   `<https://github.com/jharwell/sierra_rosbridge>`_

   The package provides the following ROS node:

   - ``sierra_timekeeper`` — Tracks elapsed time for an :term:`Experimental
     Run` and terminates it once the duration specified by ``--exp-setup`` has
     elapsed. ROS has no built-in time-bounded execution mechanism; this node
     fills that gap. SIERRA automatically inserts the corresponding XML tag into
     each ``.launch`` file it generates.

Next Steps
==========

With SIERRA installed, the fastest way to see it in action is the
:doc:`trial`, which runs a complete experiment using a pre-built sample project
with no additional setup.

If you are ready to connect SIERRA to your own code, go to :doc:`setup`.
