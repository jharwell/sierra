.. SPDX-License-Identifier:  MIT

This applies to the following ROS-based engines:

- :term:`ROS1+Gazebo`

- :term:`ROS1+Robot`

For the purposes of illustration we will use
``--expdef-template=sample.launch``:

.. code-block:: XML

    <ros-configuration>
       <master>
          ...
       </master>
       <robot>
          ...
       </robot>
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
