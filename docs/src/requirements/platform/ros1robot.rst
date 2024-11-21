.. SPDX-License-Identifier:  MIT

#. All data from multiple robots somehow ends up accessible through the
   filesystem on the host machine SIERRA is invoked on, as if the same
   experimental run was locally with a simulator. There are several ways to
   accomplish this:

   - Use SIERRA's ability to configure a "master" node on the host machine, and
     then setup streaming of robot data via ROS messages to this master
     node. Received data is processed as appropriate and then written out to the
     local filesystem so that it is ready for statistics generation during
     stage 3.

     .. IMPORTANT:: If you use this method, then you will need to handle robots
                    starting execution at slightly different times in your code
                    via (a) a start barrier triggered from the master node, or
                    else timestamp the data from robots and marshal it on the
                    master node in some fashion. The :ref:`SIERRA ROSBridge
                    <packages/rosbridge>` provides some support for (a).

   - Mount a shared directory on each robot where it can write its data, and
     then after execution finishes but before your code exits you process the
     per-robot data if needed so it is ready for statistics generation during
     stage 3.

   - Record some/all messages sent and received via one or more ROSbag files,
     and then post-process these files into a set of dataframes which are
     written out to the local filesystem.

   - Record some/all messages sent and received via one or more ROSbag files,
     and use these files directly as a "database" to query during stage 3. This
     would require writing a SIERRA storage plugin (see
     :ref:`tutorials/plugin/storage`).

     .. IMPORTANT:: This method requires that whatever is recorded into the
                    ROSbag file is per-run, not per-robot; that is, if a given
                    data source somehow built from messages sent from multiple
                    robots, those messages need to be processed/averaged/etc and
                    then sent to a dedicated topic to be recorded.

#. :envvar:`ROS_PACKAGE_PATH` is set up properly prior to invoking SIERRA on the
   local machine AND all robots are setup such that it is populated on login
   (e.g., an appropriate ``setup.bash`` is sourced in ``.bashrc``).

#. All robots have :envvar:`ROS_IP` or :envvar:`ROS_HOSTNAME` populated, or
   otherwise can correctly report their address to the ROS master. You can
   verify this by trying to launch a ROS master on each robot: if it launches
   without errors, then these values are setup properly.
