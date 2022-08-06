.. _ln-sierra-tutorials-project-models:

=============
SIERRA Models
=============

For a software engineering definition of a SIERRA model, see :term:`Plugin`.

Create A New Intra-Experiment Model
===================================

Model File Requirements
-----------------------

#. All model files need to be placed in ``<project>/models``.

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

Model Configuration
-------------------

If you add a new intra-experiment model, it will not automatically be run during
stage 4. You will need to modify the ``<project>/config/models.yaml`` file to
enable your model.


With ``<project>/config/models.yaml``, each model has the following YAML fields
under a root ``models`` dictionary:

- ``pyfile`` - The name of the python file with the ``models/`` directory for
  the project where the model name be found. This also serves as the name of the
  model within SIERRA.

Each model specified in ``models.yaml`` can take any number of parameters of any
type specified as extra fields in the YAML file; they will be parsed and passed
to the model constructor as part of ``config``.


``config/models.yaml``
^^^^^^^^^^^^^^^^^^^^^^

Root level dictionaries:

- ``models`` - List of enabled models. This dictionary is mandatory for all
  experiments (if models are enabled, that is).


Example YAML Config
###################

.. code-block:: YAML

   models:

     # The name of the python file under ``project/models`` containing one or
     # more models meeting the requirements of one of the model interfaces:
     # :class:`~models.IConcreteIntraExpModel1D`,
     # :class:`~models.IConcreteIntraExpModel2D`,
     # :class:`~models.IConcreteInterExpModel1D`.

     - pyfile: 'my_model1'
     - pyfile: 'my_model2'
       model2_param1: 17
       ...
     - ...

Any other parameters/dictionaries/etc needed by a particular model can be added
to the list above and they will be passed through to the model's constructor.
