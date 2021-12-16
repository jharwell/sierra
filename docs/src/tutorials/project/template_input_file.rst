.. _ln-tutorials-project-template-input-file:

====================
Template Input Files
====================

Template Input Files Passed to SIERRA
=====================================

Examples of the structure/required content of the XML file passed to SIERRA via
``--template-input-file`` for each supported :term:`Platform` are below.

.. tabs::

   .. tab:: ARGoS


      For a controller ``MyController``:

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

   See :ref:`ln-req-xml` for usage/description of the ``__CONTROLLER__`` tag.

   .. tab:: ROS+Gazebo (ROS parameter server)

      .. code-block:: XML

          <rosgazebo-configuration>
             <launch>
                ...
                <param name="task_alloc/mymethod/threshold" value="17"/>
                ...
             </launch>
         <rosgazebo-configuration>

   .. tab:: ROS+Gazebo (``<params>`` tag)

      .. code-block:: XML

          <rosgazebo-configuration>
             <launch>
                ...
             </launch>
             <params>
                <task_alloc>
                   <mymethod threshold="17"/>
                </task_alloc>
             </params>
          </rosgazebo-configuration>

Post-Processed Template Input Files
===================================

SIERRA may insert additional XML tags and split the processed template input
file into multiple template files, depending on the platform. The results of
this processing are shown below for each supported :term:`Platform`. No
additional modifications beyond those necessary to get use the platform with
SIERRA are shown (i.e., no :term:`Batch Criteria` modifications).

Any of the following may be inserted:

- A new tag for the configured random seed.

- A new tag for the configured experiment length in seconds.

- A new tag for the path to a second XML file containing all controller XML
  configuration.

.. tabs::

   .. tab:: ARGoS

      For a controller ``MyController``:

      .. code-block:: XML

         <argos-configuration>
            ...
            <controllers>
               <MyController>
                  <params>
                     <task_alloc>
                        <mymethod threshold="17"/>
                     </task_alloc>
                  </params>
               </MyController>
            </controllers>
            ...
        <argos-configuration>

   .. tab:: ROS (ROS parameter server)

      .. code-block:: XML

          <rosgazebo-configuration>
             <launch>
                ...
                <node name="sierra_timekeeper" pkg="sierra_rosbridge" type="sierra_timekeeper.py" required="true"/>
                <param name="task_alloc/mymethod/threshold" value="17"/>
                <param name="sierra/experiment/length" value="1234">
                <param name="sierra/experiment/random_seed" value="5678">
                ...
             </launch>
         <rosgazebo-configuration>


      The simulation length configured via ``--time-setup`` is added as a ROS
      parameter; used by the SIERRA timekeeper node (see
      :ref:`ln-packages-rosbridge`).

   .. tab:: ROS+Gazebo (``<params>`` tag)

      In the ``.launch`` file:

      .. code-block:: XML

         <launch>
            ...
            <node name="sierra_timekeeper" pkg="sierra_rosbridge" type="sierra_timekeeper.py" required="true"/>
            <param name="sierra/experiment/param_file" value="/path/to/file">
            ...
         </launch>

      In the ``.params`` file:

      .. code-block:: XML

          <params>
             <sierra>
                <experiment random_seed="1234"
                            length="5678"/>
             </sierra>
             <task_alloc>
                <mymethod threshold="17"/>
             </task_alloc>
          </params>


      The simulation length configured via ``--time-setup`` is added as an XML
      parameter; used by the SIERRA timekeeper node (see
      :ref:`ln-packages-rosbridge`).
