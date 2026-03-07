.. _tutorials/project/hooks:

============================
SIERRA Pipeline Python Hooks
============================

SIERRA allows a number of different elements of its pipeline to be customized
and extend by a :term:`Project`. To override part of a stage of the SIERRA
pipeline, you must create a ``pipeline/stageX`` directory structure in your
project directory, where ``stageX`` is the stage you want to override part of.

.. NOTE:: This is the most advanced feature of SIERRA, and strange things may
          happen or things might not work right if you don't call the
          ``super()`` version of whatever functions you are overriding in your
          hook.

.. WARNING:: Don't try to override parts of the pipeline which are not listed
             below. It will probably not work, and even if it does there is
             every chance that it will break stuff.

Multi-Stage Hooks
=================

Base Batch Criteria
-------------------

Suppose you want to extend one of the following core SIERRA classes to add
additional attributes/methods you want to be accessible to all :term:`Batch
Criteria` in your project:

- :class:`~sierra.core.variables.batch_criteria.BaseBatchCriteria`

- :class:`~sierra.core.variables.batch_criteria.UnivarBatchCriteria`

- :class:`~sierra.core.variables.batch_criteria.XVarBatchCriteria`

To do this, do the following:

#. Create ``variables/batch_criteria.py`` in the root directory for your
   project.

#. Override one or more of the classes above, and SIERRA will then select your
   version of said override classes when running. Exactly where SIERRA is
   looking/what module it uses when a given class is requested can be seen with
   ``--log-level=TRACE``.

.. WARNING:: Don't override or extend any of the interfaces! It will causes
             static analysis and/or runtime errors.

Stage 4 Hooks
=============

Tiered YAML Config
------------------

Suppose you have some graphs which are common to multiple SIERRA projects, and
you don't want to have to duplicate the graph definitions in the ``.yaml``
files. You can put those definitions in a single location and then add them to
the ``.yaml`` graph definitions that are unique to the :term:`Project` as
follows:

#. Create ``pipeline/stage4/graphs/loader.py``.

#. Extend/override the
   :func:`sierra.core.pipeline.yaml.load_config()` function:

   .. code-block:: python

      import sierra.core.pipeline import yaml
      from sierra.core import types

      def load_config(cmdopts: types.Cmdopts, name: str) -> tp.Optional[types.YAMLDict]:
          ...
