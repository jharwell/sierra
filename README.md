# SIERRA (Swarm robotics simulation automation framework)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

## Setup

1. Get an MSI account (you will need to talk to Maria Gini, my advisor).

2. Login to MSI and setup the build environment:

        . /home/gini/shared/swarm/bin/build-env-setup.sh

3. Clone and build the devel branch of the project and all its sub
   repositories:

         /home/gini/shared/swarm/bin/clone-and-build-clean.sh $HOME/git

   The argument is the root directory where all repositories should be
   cloned/built. It can be anywhere you have write access to.

   If you want to squeeze maximum performance out of the code, then you can
   recompile also pass `-DWITH_ER_NREPORT=yes` (in addition to the other
   arguments the script passes to cmake) which will turn off ALL diagnostic
   logging (metrics are still logged). It can be significantly faster, but if
   the results look weird/something goes wrong you will not have the usual
   logs available to troubleshoot/debug.

4. Modify the `template.pbs` file in this repo for your experiment/batch
   experiment. `sierra` has a lot of options, and the help for each is fairly
   intuitive.

6. Submit your job on MSI with:

        qsub your-pbs-script.pbs

7. Reap the rewards of research!
