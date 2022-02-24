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

      For the purposes of illustration we will use
      ``--template-input-file=sample.argos`` and a controller ``MyController``:

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

   .. tab:: ROS (Using parameter server)

      For the purposes of illustration we will use
      ``--template-input-file=sample.launch``


      .. code-block:: XML

          <ros-configuration>
             <master>
                ...
                <param name="metrics/directory" value="/path/to/dir"/>
                ...
             </master>
             <robot>
                ...
                <param name="task_alloc/mymethod/threshold" value="17"/>
                <param name="motion/random_walk" value="0.1"/>
                ...
             </robot>
         <ros-configuration>

   .. tab:: ROS (Using ``<params>`` tag)

      For the purposes of illustration we will use
      ``--template-input-file=sample.launch``

      .. code-block:: XML

          <ros-configuration>
             <master>
                ...
             </master>
             <params>
                <metrics directory="/path/to/dir"/>
                <task_alloc>
                   <mymethod threshold="17"/>
                </task_alloc>
                <motion>
                   <random_walk prob="0.1"/>
                </motion>
             </params>
          </ros-configuration>

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

- A new tag for the configured # robots.

- A new tag for the controller rate (ticks per second).

- A new tag for the path to a second XML file containing all controller XML
  configuration.

.. tabs::

   .. tab:: ARGoS

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

      No tags are insert by SIERRA input the input ``.argos`` file.

   .. tab:: ROS (Using parameter server)

      Input ``sample.launch`` file is split into (potentially) two files:

        - ``sample_robot.launch`` containing the ``<robot>`` tag in the original
          input file, which is changed to ``<launch>``. This has all nodes and
          configuration which is robot-specific and/or will be launched on each
          robot.

        - ``sample_master.launch`` containing the ``<master>`` tag in the
          original input file, which is changed to ``<launch>``. This has all
          the nodes and configuration which is ROS master-specific and will be
          launched on the SIERRA host machine (which where the ROS master will
          be set to).

      ``sample_robot.launch`` file:

      .. code-block:: XML

         <launch>
            ...
            <param name="task_alloc/mymethod/threshold" value="17"/>
            <param name="motion/random_walk" value="0.1"/>
            ...
            <group ns='sierra'>
               <param name="experiment/length" value="1234"/>
               <param name="experiment/random_seed" value="5678"/>
               <param name="experiment/param_file" value="/path/to/file"/>
               <param name="experiment/n_robots" value="123"/>
               <param name="experiment/ticks_per_sec" value="5"/>
            </group>
            ...
         </launch>

      ``sample_master.launch`` file:

      .. code-block:: XML

         <launch>
            ...
            <param name="metrics/directory" value="/path/to/dir"/>
            ...
            <group ns='sierra'>
               <node name="sierra_timekeeper" pkg="sierra_rosbridge" type="sierra_timekeeper.py" required="true"/>
               <param name="experiment/length" value="1234"/>
               <param name="experiment/random_seed" value="5678"/>
               <param name="experiment/param_file" value="/path/to/file"/>
               <param name="experiment/n_robots" value="123"/>
               <param name="experiment/ticks_per_sec" value="5"/>
            </group>
            ...
         </launch>

   .. tab:: ROS (Not using parameter server)

      Input ``sample.launch`` file is split into (potentially) three files:

        - ``sample_robot.launch`` containing the ``<robot>`` tag in the original
          input file, which is changed to ``<launch>``. This has all nodes and
          configuration which is robot-specific and/or will be launched on each
          robot.

        - ``sample_master.launch`` containing the ``<master>`` tag in the
          original input file, which is changed to ``<launch>``. This has all
          the nodes and configuration which is ROS master-specific and will be
          launched on the SIERRA host machine (which where the ROS master will
          be set to).

        - ``sample.params`` containing the ``<params>`` tag in the original
          input file, which is written out as a common file to use to share
          parameters between the robots and the ROS master.

      Processed ``sample_robot.launch`` file:

      .. code-block:: XML

          <launch>
             ...
             <group ns='sierra'>
                <param name="experiment/length" value="1234"/>
                <param name="experiment/random_seed" value="5678"/>
                <param name="experiment/param_file" value="/path/to/file"/>
                <param name="experiment/n_robots" value="123"/>
                <param name="experiment/ticks_per_sec" value="5"/>
             </group>
             ...
          </launch>


      Processed ``sample_master.launch`` file:

      .. code-block:: XML

          <launch>
             ...
             <group ns='sierra'>
                <node name="sierra_timekeeper" pkg="sierra_rosbridge" type="sierra_timekeeper.py" required="true"/>
                <param name="experiment/length" value="1234"/>
                <param name="experiment/random_seed" value="5678"/>
                <param name="experiment/param_file" value="/path/to/file"/>
                <param name="experiment/n_robots" value="123"/>
                <param name="experiment/ticks_per_sec" value="5"/>
             </group>
             ...
          </launch>


      Processed ``sample.params`` file:

      .. code-block:: XML

          <params>
             <metrics directory="/path/to/dir"/>
             <motion>
                <random_walk prob="0.1"/>
             </motion>
             <task_alloc>
                <mymethod threshold="17"/>
             </task_alloc>
          </params>
