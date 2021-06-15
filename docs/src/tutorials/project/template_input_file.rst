.. _ln-tutorials-project-template-input-file:

===================
Template Input File
===================

The file passed to ``--template-input-file`` has a few formatting requirements
to be used by SIERRA.

#. Instead of specifying the name of the controller you want to use under the
   ``<controllers>`` tag directly like this for a controller named
   ``mycontroller``:

   .. code-block:: XML

      ...
      <controllers>
         <mycontroller>
            ...
         </mycontroller>
      </controllers>
      ...

   You need specify the controller to use via a placeholder tag
   ``__controller__`` like this:

   .. code-block:: XML

      ...
      <controllers>
         <__controller__>
            ...
         </__controller__>
      </controllers>
      ...

   This makes auto-population of the controller name based on the
   ``--controller`` argument and the contents of ``controllers.yaml`` (see
   :doc:`main_config` for details) in template input files possible in SIERRA.
