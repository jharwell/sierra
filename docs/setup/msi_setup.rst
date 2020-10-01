.. _ln-msi-setup:

MSI Setup
=========

.. IMPORTANT::
   Prior to executing these steps you should:

   #. Have completed the :ref:`ln-local-setup` guide.
   #. Have read through :ref:`ln-usage` guide, and gotten **CORRECT** results
      on some small scale experiments of interest on your local machine.

You really, really, *really*, don't want to be trying to do
development/debugging on MSI.

#. Get an MSI account (you will need to talk to Maria Gini, my advisor), and
   verify that you can login to ``mesabi`` via the following commands, run from
   your laptop on a UMN computer/UMN wifi (will not work from outside UMN campus
   without a VPN)::

     ssh <x500>@login.msi.umn.edu
     ssh mesabi.msi.umn.edu


   Where ``<x500>`` is your umn x500. If the commands are successful, you have
   logged into a ``mesabi`` login node (this is different than a ``mesabi``
   compute node).

   A similar check for ``gangi`` via the following commands, run from your
   laptop on a UMN computer/UMN wifi (will not work from outside UMN campus
   without a VPN)::

     ssh <x500>@login.msi.umn.edu
     ssh gangi.msi.umn.edu

   If the commands are successful, you have logged into a ``gangi`` login node
   (this is different than a ``gangi`` compute node).

#. Once you can login, you can begin the setup by sourcing the environment
   definitions::

     . /home/gini/shared/swarm/bin/msi-env-setup.sh

   .. IMPORTANT:: ANYTIME you log into an MSI node (login or compute) to
                  build/run ANYTHING you MUST source this script otherwise
                  things will (probably) not work. This includes if you ran the
                  script on a login node and then started an interactive session
                  via job submission with ``-I`` (the environment is NOT
                  inherited).

#. On an MSI login node (can be any type, as the filesystem is shared across all
   clusters), install the same python dependencies as in :ref:`ln-usage`, but
   user local (you obviously don't have admin priveleges on the cluster)::

     pip3 install --user -r requirements/msi.txt

   This is a one time step. Must be done on a login node, as compute nodes do
   not always have internet access (apparently?).

#. On an MSI login node (can be any type, as the filesystem is shared across all
   clusters), run the bash script to clone the project::

     /home/gini/shared/swarm/bin/msi-clone-all.sh $HOME/git

   The 1st argument is the path (relative or absolute) to the location where you
   want the project repos to live (they will all be cloned into that level).

   If you need to checkout a particular branch in the repo you can do that after
   running the script (or copy the script and modify it to do this automatically
   if you are going to be doing a lot of work on MSI).

#. On an MSI login node, get an interactive job session so you can build your
   selected project and its dependencies natively to the cluster you will be
   running on (gangi/mesabi) for maximum speed::

     qsub -I -lwalltime=1:00:00,nodes=1:ppn=8,mem=20gb

   The above command, when it returns, will give you 1 hour of time on an actual
   compute node. You know you are running/building on a compute node rather than
   a login node on gangi/mesabi when the hostname is ``cnXXXX`` rather than
   ``lnXXXX``.

#. In your interactive session run the bash script to build the project (note
   that you may want to tweak the cmake defines in the script, or use your own
   script, depending on what types of experiments you are running)::

     /home/gini/shared/swarm/bin/msi-build-default.sh $HOME/git 8

   * 1st arg: The root directory where all where cloned into with the
     ``msi-clone-all.sh`` script. In the example above, this is ``$HOME/git``.

   * 2nd arg: How many cores to use when building (should be the same # as the
     ppn when you submitted your interactive job session. In the example above
     this is 8.
