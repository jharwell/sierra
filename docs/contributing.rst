Contributing
============

To contribute to the SIERRA core, in you should follow the general workflow
outlined in :xref:`LIBRA`. For the static analysis step:

#. Install additional dependencies::

     pip3 pytype pylint mypy

#. Run the following on the code from the root of SIERRA::

     pytype -k core plugins

   Fix ANY and ALL errors that arise, as SIERRA should get a clean bill of health
   from the checker.

#. Run the following on any module directories you changed, from the root of
   SIERRA::

     pylint <directory name>

   Fix ANY errors your changes have introduced (there will probably still be
   errors in the pylint output, because cleaning up the code is always a work in
   progress).

#. Run the following on any module directories you changed, from the root of
   SIERRA::

     mypy --ignore-missing-imports --warn-unreachable core plugins

   Fix ANY errors your changes have introduced (there will probably still be
   errors in the my output, because cleaning up the code is always a work in
   progress).
