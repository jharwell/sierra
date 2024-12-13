Within this file, you may define the following classes, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them. If you omit
a required class, you will get an error on SIERRA startup. If you try to use
a part of SIERRA which requires an optional class you omitted, you will get a
runtime error.

.. list-table:: Platform Plugin Classes
   :widths: 25,25,50
   :header-rows: 1

   * - Class

     - Required?

     - Conforms to interface?

   * - ExpRunShellCmdsGenerator

     - No

     - :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`

   * - ExpShellCmdsGenerator

     - No

     - :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`



Within this file, you may define the following functions, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them. If you try
to use a part of SIERRA which requires an optional function you omitted, you
will get a runtime error.

.. list-table:: Execution Environment Plugin Functions
   :widths: 25,25,75
   :header-rows: 1

   * - Function

     - Required?

     - Purpose

   * - cmdline_postparse_configure()

     - No

     - Performs additional modification/insertion of parsed cmdline arguments,
       as well as any needed validation for this execution environment.

       Used in stages 1-5.

   * - exec_env_check()

     - No

     - Performs checking of the software environment for this execution
       environment prior to running anything in stage 2.

Below is a sample/skeleton ``plugin.py`` to use as a starting point.

.. code-block:: python

   from sierra.core.experiment import bindings

   @implements.implements(bindings.IExpRunShellCmdsGenerator)
   class ExpRunShellCmdsGenerator():
      """
      A class that conforms to
      :class:`sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.

      """

   @implements.implements(bindings.IRunShellCmdsGenerator)
   class ExpShellCmdsGenerator():
      """
      A class that conforms to
      :class:`sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

      """

   def exec_env_check(cmdopts: types.Cmdopts):
       """
       Check the software environment (envvars, PATH, etc.) for this execution
       environment plugin prior to running anything in stage 2.
       """

   def cmdline_postparse_configure(argparse.Namespace) -> argparse.Namespace:
       """
       Additional configuration and/or validation of the passed cmdline
       arguments pertaining to this execution environment. Validation should be
       performed with assert(), and the parsed argument object should be
       returned with any modifications/additions.
       """
