How to Add A New Intra-Experiment Model
=======================================

If you add a new intra-experiment model, it will not automatically be run during
stage 4. You will need to modify the ``models.yaml`` file to enable your model.


With ``models.yaml``, each model has the following YAML fields under a root
``models`` dictionary:

- ``pyfile`` - The name of the python file with the ``models/`` directory for
  the project where the model name be found. This also serves as the name of the
  model within SIERRA.


Model File Requirements
-----------------------

#. All model files need to be placed in ``<project_root>/models``.

#. Not all classes in a model ``.py`` must be models.

#. All model ``.py`` files must define an ``available_models()`` function which
   takes a string argument for the type of model [ ``intra``, ``inter`` ] and
   returns a list of the names of the intra- and inter-experiment models present
   in the file. This allows the user flexibility to group multiple related
   models together in the same file, rather than requiring 1 model per ``.py``
   file.

#. All model classes in the model ``.py`` must implement an appropriate
   interface interface of ``<sierra>/models/interface.py``, depending on whether
   the model is 1D or 2D, and whether or not it is an intra-experiment or
   inter-experiment model.
