.. SPDX-License-Identifier:  MIT

Input ``sample.launch`` file is split into multiple files within the
:ref:`usage/run-time-tree`:

  - ``sample_runX_robotY.launch`` containing the ``<robot>`` tag in the
    original input file, which is changed to ``<launch>``. This has all
    nodes and configuration which is robot-specific and/or will be
    launched on each robot ``Y`` for each run ``X``.

  - ``sample_master_runX.launch`` containing the ``<master>`` tag in the
    original input file, which is changed to ``<launch>``. This has all
    the nodes and configuration which is ROS master-specific and will be
    launched on the SIERRA host machine (which where the ROS master will
    be set to) for each run ``X``.

``sample_run0_robot0.launch`` file:

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
         <param name="experiment/n_agents" value="123"/>
         <param name="experiment/ticks_per_sec" value="5"/>
      </group>
      ...
   </launch>

``sample_master_run0.launch`` file:

.. code-block:: XML

   <launch>
      ...
      <param name="metrics/directory" value="/path/to/dir"/>
      ...
      <group ns='sierra'>
         <node
            name="sierra_timekeeper"
            pkg="sierra_rosbridge"
            type="sierra_timekeeper.py"
            required="true"
            output="screen"/>
         <param name="experiment/length" value="1234"/>
         <param name="experiment/random_seed" value="5678"/>
         <param name="experiment/param_file" value="/path/to/file"/>
         <param name="experiment/n_agents" value="123"/>
         <param name="experiment/ticks_per_sec" value="5"/>
      </group>
      ...
   </launch>
