.. _ln-sierra-tutorials-project-new-bc:

===========================
Create A New Batch Criteria
===========================

If you have a new experimental variable that you have added to your C++ library,
**AND** which is exposed via the input ``.xml`` file, then you need to do the
following to get it to work with SIERRA as a :term:`Batch Criteria`:

#. Make your variable (``MyVar`` in this tutorial) inherit from
   :class:`sierra.core.variables.batch_criteria.UnivarBatchCriteria` and place
   your ``my_var.py`` file under ``<project>/variables/``. The class defined in
   ``my_var.py`` should be a "base class" version of your variable, and
   therefore should take in parameters, and NOT have any hardcoded values in it
   anywhere (i.e., rely on dynamic class creation via the ``factory()``
   function). This is to provide maximum flexibility to those using SIERRA, so
   that they can create `any` kind of instance of your variable, and not just
   the ones you have made pre-defined classes for.

#. Define the abstract functions from
   :class:`sierra.core.variables.batch_criteria.UnivarBatchCriteria`. Most are
   straight forward to understand from the documentation, but the XML
   manipulation ones warrant more explanation.

   .. _ln-xpath: https://docs.python.org/2/library/xml.etree.elementtree.html

   In order to change attributes, add/remove tags, you will need to understand
   the XPath syntax for search in XML files; tutorial is `here _ln-xpath`.

   ``get_attr_changelist()`` - Given whatever parameters that your variable was
   passed during initialization (e.g. the boundaries of a range you want to vary
   it within), produce a list of sets, where each set is all changes that need
   to be made to the ``.xml`` template file in order to set the value of your
   variable to something. Each change is a
   :class:`~sierra.core.experiment.xml.AttrChange` object, that takes the
   following arguments in its constructor:

   #. XPath search path for the **parent** of the attribute that you want to
      modify.

   #. Name of the attribute you want to modify within the parent element.

   #. The new value as a string (integers will throw an exception).

   ``gen_tag_rmlist()`` - Given whatever parameters that your variable was
   passed during initialization, generate a list of sets, where each set is all
   tags that need to be removed from the ``.xml`` template file in order to
   set the value of your variable to something.

   Each change is a :class:`~sierra.core.experiment.xml.TagRm` object that
   takes the following arguments in its constructor:

   #. XPath search path for the **parent** of the tag that you want to
      remove.

   #. Name of the tag you want to remove within the parent element.

   ``gen_tag_addlist()`` - Given whatever parameters that your variable was
   passed during initialization, generate a list of sets, where each set is all
   tags that need to be added to the ``.xml`` template file.

   Each change is a :class:`~sierra.core.experiment.xml.TagAdd` object that
   takes the following arguments in its constructor:

   #. XPath search path for the **parent** of the tag that you want to
      add.

   #. Name of the tag you want to add within the parent element.

   #. A dictionary of (attribute, value) pairs to create as children of the
      tag when creating the tag itself.

#. Define the parser for your variable in order to parse the command line string
   defining your batch criteria into a dictionary of attributes that can then be
   used by the ``factory()``. The parser can be defined anywhere, though it must
   be able to be used in the ``factory()`` function. The parse class must
   conform to the following interface:

   .. code-block:: python

      class MyVarParser():
          ...
      def __call__(self, cli_arg: str) -> dict:
          ...

   It must be callable with a single argument which is whatever was passed to
   ``--batch-criteria``. See
   :class:`sierra.core.variables.population_size.Parser` for a simple example of
   this.

#. Define a factory function to dynamically create classes from the base class
   definition of ``MyVar`` in ``my_var.py``. It must have the following
   signature:

   .. code-block:: python

      import pathlib

      def factory(cli_arg: str,
                  main_config: dict,
                  batch_input_root: pathlib.path,
                  **kwargs) -> MyVar:
      """
      Arguments:

          cli_arg: The string of the your batch criteria/variable you
                   have defined that was passed on the command line via
                   ``--batch-criteria``.
          main_config: The main YAML configuration dictionary
          (``<project>/config/main.yaml``).

          batch_input_root: The directory where the experiment directories are
                            to be created.

          **kwargs: Additional arguments required by this batch criteria. This
          may be used during stage 5 to pass the ``--scenario`` if needed.

      """

   This function should do the following:

   #. Call the parser for your variable, as defined above.

   #. Return a custom instance of your class that is named according to the
      specific batch criteria string passed on the command line which inherits
      from ``MyVar`` variable base class you defined above, and that has an
      ``__init__()`` function that calls the ``__init__()`` function of your
      base variable. To dynamically create a new class which is derived from
      your ``MyVar`` class, you can use the ``type()`` function.

   See ``<sierra>/plugins/argos/variables/population_size.py`` for a simple
   example of this.
