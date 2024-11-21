.. SPDX-License-Identifier:  MIT

For the purposes of illustration we will use
``--expdef-template=sample.argos`` and a controller ``MyController``:

.. code-block:: XML

   <argos-configuration>
      ...
      <controllers>
         <__CONTROLLER__>
            ...
            <params>
               <task_alloc>
                  <mymethod threshold="17"/>
               </task_alloc>
            </params>
         </__CONTROLLER__>
      </controllers>
      ...
  <argos-configuration>


See :ref:`req/expdef` for usage/description of the ``__CONTROLLER__`` tag in XML
files.
