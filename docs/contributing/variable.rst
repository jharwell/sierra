How to Add A New Variable
=========================

If you have a new experimental variable that you have added to the main fordyca
library, **AND** which is exposed via the input ``.argos`` file, then you need to do
the following to get it to work with sierra as a batch criteria:

#. Make your variable (``MyVar`` in this tutorial) inherit from
   ``UnivarBatchCriteria`` and place your ``my_var.py`` file under
   ``variables/``. The "base class" version of your variable should take in
   parameters, and NOT have any hardcoded values in it anywhere (i.e. rely on
   dynamic class creation via the ``Factory()`` function).

#. Define the parser for your variable in a separate ``my_var_parser.py`` file
   in order to parse the command line string defining your batch criteria into a
   dictionary of attributes that can then be used by the ``Factory()``, which
   must be defined in the variable ``my_var.py``

#. Define the abstract functions from ``UnivarBatchCriteria``. Most are straight
   forward to understand from the documentation, but the XML manipulation ones
   warrant more explanation.

   .. _ln-xpath: https://docs.python.org/2/library/xml.etree.elementtree.html

   In order to change attributes, add/remove tags, you will need to understand
   the XPath syntax for search in XML files; tutorial is `here _ln-xpath_`.

   ``get_attr_changelist()`` - Given whatever parameters that your variable was
   passed during initialization (e.g. the boundaries of a range you want to vary
   it within), produce a list of sets, where each set is all changes that need
   to be made to the .argos template file in order to set the value of your
   variable to something. Each change is a tuple with the following elements:

   #. XPath search path for the **parent** of the attribute that you want to
      modify.

   #. Name of the attribute you want to modify within the parent element.

   #. The new value as a string (integers will throw an exception).

   ``gen_tag_rmlist()`` - Given whatever parameters that your variable was
   passed during initialization, generate a list of sets, where each set is all
   tags that need to be removed from the .argos template file in order to set
   the value of your variable to something.

   Each change is a tuple with the following elements:

   #. XPath search path for the **parent** of the tag that you want to
      remove.

   #. Name of the attribute you want to remove within the parent element.

   ``gen_tag_addlist()`` - Given whatever parameters that your variable was
   passed during initialization, generate a list of sets, where each set is all
   tags that need to be added to the .argos template file.

   Each change is a tuple with the following elements:

   #. XPath search path for the **parent** of the tag that you want to
      add.

   #. Name of the tag you want to add within the parent element.

   #. A dictionary of (attribute, value) pairs to create as children of the
      tag when creating the tag itself.

   ``Factory(cmdline_str, main_config, batch_generation_root, **kwargs)`` -

   Given:

      - The string of the your batch criteria/variable you have defined that
        was passed on the command line

      - The main YAML configuration dictionary

      - The directory where the experiment directories are to be created, create
        specific instances of your variable that are derived from your "base"
        variable class. This is to provide maximum flexibility to those using
        sierra, so that they can create `any` kind of instance of your variable,
        and not just the ones you have made pre-defined classes for.

   This function is a class factory method, and should (1) call the parser for
   your variable, (2) return a custom instance of your class that is named
   according to the specific batch criteria string passed on the command line,
   inherits from the "base" variable class you defined above, and that has an
   ``__init__()`` function that calls the ``__init__()`` function of your base
   variable

   See ``variables/population_size.py`` for a simple example of this.

#. Once finished open a pull request with your new variable.
