.. SPDX-License-Identifier:  MIT

This applies to the following ROS1-based engines:

- :term:`ROS1+Gazebo`

- :term:`ROS1+Robot`

For the purposes of illustration we will use
``--expdef-template=sample.launch``:

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
