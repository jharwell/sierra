.. SPDX-License-Identifier:  MIT

The provided ``--expdef-template`` will look like this when populated within
:ref:`usage/run-time-tree`:

.. code-block:: XML

   <argos-configuration>
      ...
      <controllers>
         <MyController>
            ...
            <params>
               <task_alloc>
                  <mymethod threshold="17"/>
               </task_alloc>
            </params>
         </MyController>
      </controllers>
      ...
   <argos-configuration>

No tags are inserted by SIERRA, and the file is not further split by SIERRA.
