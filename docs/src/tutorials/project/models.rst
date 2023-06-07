.. _ln-sierra-tutorials-project-models:

====================================
Adding Models to your SIERRA Project
====================================

Models can be written in any language, but if they aren't python, you will have
to write some python bindings to translate the inputs/outputs into things that
SIERRA can understand/is expecting.

Create A New Intra-Experiment Model
===================================

#. Look at:

   - :class:`~sierra.core.models.interface.IConcreteIntraExpModel1D`
   - :class:`~sierra.core.models.interface.IConcreteIntraExpModel2D`
   - :class:`~sierra.core.models.interface.IConcreteInterExpModel1D`

   to determine if one of the model types SIERRA already supports will work for
   you. If one will, great! Otherwise, you'll probably need to add a new one.

#. Define your models and/or their bindings in one or more ``.py`` files under
   ``<project>/models``. Not all python files in ``<project>/models`` have to
   contain models! See `Model File Requirements`_ below for details about what
   needs to be in python files which *do* contain models/model bindings.

#. Enable your model. If you add a new intra-experiment model, it will not
   automatically be run during stage 4. You will need to modify the
   ``<project>/config/models.yaml`` file to enable your model. See `Model
   Configuration`_ below for details.

#. Run your model during stage 4. You also need to pass ``--models-enable``
   (models are not enabled by default); see :ref:`ln-sierra-usage-cli` for more
   details.

Model File Requirements
-----------------------

#. Must be under ``<project>/models``.

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


With ``<project>/config/models.yaml``, each model has the following YAML fields
under a root ``models`` dictionary:

- ``pyfile`` - The name of the python file with the ``models/`` directory for
  the project where the model name be found. This also serves as the name of the
  model within SIERRA.

Each model specified in ``models.yaml`` can take any number of parameters of any
type specified as extra fields in the YAML file; they will be parsed and passed
to the model constructor as part of ``config``. See below for an example.


``config/models.yaml``
^^^^^^^^^^^^^^^^^^^^^^

Root level dictionaries:

- ``models`` - List of enabled models. This dictionary is mandatory for all
  experiments during stage 4 (if models are enabled via ``--models-enabled````,
  that is).


Example YAML Config
###################

.. code-block:: YAML

   models:

     # The name of the python file under ``project/models`` containing one or
     # more models meeting the requirements of one of the model interfaces:
     # :class:`~sierra.core.models.interface.IConcreteIntraExpModel1D`
     # :class:`~sierra.core.models.interface.IConcreteIntraExpModel2D`
     # :class:`~sierra.core.models.interface.IConcreteInterExpModel1D`

     - pyfile: 'my_model1'
       fooparam: 42
       barparam: "also 42"

     - pyfile: 'my_model2'
       param1: 17
       param2: "abc"
       ...
     - ...

Any other parameters/dictionaries/etc needed by a particular model can be added
to the list above and they will be passed through to the model's constructor.

Creating A New Inter-Experiment Model
=====================================

TODO!
