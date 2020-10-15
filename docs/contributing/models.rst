How to Add A New Intra-Experiment Model
=======================================

If you add a new intra-experiment model, it will not automatically be run during
stage 4. You will need to modify the ``models.yaml`` file to enable your model.


With ``models.yaml``, each model has the following YAML fields, which are parsed
into a python dictionary:

- ``src`` - Information about the model source.

  - ``py`` - The name of the python file with the ``models/`` directory for the
    project where the model name be found. This also serves as the name of the
    model within SIERRA.

  - ``class`` - The name of the python class within the ``.py`` source file
    contaning the model.

- ``target`` - Information about what graph to attach the results of the model
  to.

  - ``csv_stem`` - The name of the ``.csv`` file in the intra-experiment output
    directory, sans extension, which the model should be added to.

  - ``col`` - The name of the column within the model dataframe containing to
    add to the target ``.csv``.

- ``params`` - Any addition parameters your model needs can go here.

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

#. All model classes in the model ``.py`` must describe the functions from the
   :class:`models.model.IConcreteModel` interface of ``<sierra>/models/model.py``.


How to Add A New Inter-Experiment Model
=======================================

You can't currently, because this doesn't work in SIERRA yet.
