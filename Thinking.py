'''
6/6/2018
PINNED

By: London

This is normally a file I create for my projects.
When I'm making design decisions or have interesting thoughts about a project, they usually go in here.

This serves sort of as a "diary" for the project, helping me to remember why I made certain decisions and helping other people who read it to understand what I was thinking.
I make it a .py file because I like separating the comments out with the three quotes. It might be best off as a .txt file, but for now, I'll stick with my usual.
'''

'''
PINNED

Here are the meanings behind some comment tage I generally have in my projects:

# TODO
    something really should be done before this project iteration is finished

# upgrade
    I can see a better way of doing this, but what I have now works

# restriction
    The program is making some assumption about data that may have an impact on programs outside this one (if bugs occur, it might be because someone violated one of these restrictions)
'''

'''
6/6/2018

Okay, let's list out the goals of this project.
The overall goal is to create something that will run a bunch of experiments with different parameters, collect the data, possibly average it, and then generate graphs from the data.
It's called Sierra just because John called it Sierra, and it sounds cool to me so I'm keeping it like that for now.
He recommended I use python for running scripts, but I can also use GNUParallel to run things in parallel as well.
The hope is to be able to run the program on the supercomputers here.

Goals (in order of what I should do first):
1. Create a Python class that allows for the easy manipulation of XML
2. Hook up GNUParallel and see if I can run multiple experiments at once.
3. Use Pandas or something similar to average values and create graphs.

I want to look at the XML files. John said they were in the exp folder of the main project.
'''

'''
6/6/2018

Okay, so I now have a class that can edit and save xml files pretty easily.
'''

'''
6/6/2018
Okay, so the next goal is to create a class that takes a path to:
* An XML file specifying the setup for the experiment
* A folder containing the code for the experiment
* A folder where the modified XML files should be stored
* A folder where the graphs should be stored

Then, it should copy the XML file and create different seeds for each experiment, run each experiment in parallel, collect all the data needed, combine it together, and create graphs.
'''

'''
6/7/2018

Just copying some terminal output that will help me remember where certain folders are and how this is organized.
$ ls output/
2018-6-7:14-17
$ ls output/2018-6-7\:14-17/
fb0.log   fb11.log  fb13.log  fb15.log  fb2.log  fb4.log  fb6.log  fb8.log  metrics
fb10.log  fb12.log  fb14.log  fb1.log   fb3.log  fb5.log  fb7.log  fb9.log  sim.log
$ ls output/2018-6-7\:14-17/metrics/
block-acquisition-stats.csv  block-stats.csv  block-transport-stats.csv  distance-stats.csv

So, I tried deleting both visualization tags, and that failed, but deleting the bottom visualization tag seemed to work.
It then ran without doing a visualization.
So, I'm going to need to add something into the xml helper to delete tags, and it may need to be specific.
'''

'''
6/8/2018

Wow, deleting stuff was a lot harder than I expected, because I had to get the elements, not just the tags.
I might want to convert some of the older functions to returning elements as well, but for now this works.

I decided to make all the functions that deal with path lists private, because I think people should just be putting in paths, not path lists.

Since I started creating a lot of useless functions, I used a tool called Pyan to track which functions were calling which.
The results of this are in pyan_output.dot, and you can copy/paste that file into http://www.webgraphviz.com/ to see the output.
(Note from 6/17/2018: I have since deleted the pyan_output.dot file. If you would like to see it, you will need to re-generate it.)
'''

'''
6/11/2018

So, the goal is by the end of this week to have something that can be tested out on MSI.
This will need to:
Take a configuration file
Remove the visualization component of the file.
Set a random seed.
Add a command to run the config file to a command file.

Then, someone will run the commands.

After those are done, I'll have another part that combines the CSVs together.
'''

'''
The code deals with loose strict stuff pretty badly right now.
I added a TODO in the code to address it.
I think the biggest thing to fix it is to follow the model of generators, where we create a generator all the possible options, and then just iterate through one by one.

From https://www.msi.umn.edu/support/faq/how-can-i-use-gnu-parallel-run-lot-commands-parallel :
You have a file named commands.txt containing a list of multi-threaded commands and want to run one command per node on multiple nodes:
$ module load parallel
$ sort -u $PBS_NODEFILE > unique-nodelist.txt
$ parallel --jobs 1 --sshloginfile unique-nodelist.txt --workdir $PWD < commands.txt
'''

'''
6/13/2018

I just ran my first job on MSI. It was pretty easy and quick.
Now I'm going to do a basic script that should display the ability to use the one system folder to create working directories to use.
So, I think what I want to do is have a python script that takes in parameters and generates a command file with a particular name.
Then, I'll have the pdb file use that file to run a bunch of things in parallel.
'''

'''
6/19/2018

Finally got the experiment runner up and running experiments on my computer.
About to test it on MSI to see how it works.
Need to find a way to get this onto MSI and working.

Currently need
1. Fordyca on MSI
2. Ability to run argos projects on MSI (right now the argos3 command is not being recognized)

John recommended htop for viewing things on MSI
'''

'''
6/20/2018

Okay, finally got Argos up and running on MSI.
Now I just need to test this.
How is this supposed to work?

I think what it should do is you create your .pbs file in the form:
#!/bin/bash -l
#PBS -l walltime=8:00:00,nodes=3:ppn=8,pmem=1000mb
#PBS -m abe
#PBS -M sample_email@umn.edu
module load python3
cd sierra
python3 experiment_runner.py [options]

And then let python3 run its magic.
I just want to do a basic test to make sure it works.
I can't ensure that it will actually use all the cores yet, but if it at least runs that will be great.

For now I'll just run 3.

Current documentation for reference:
usage: experiment_runner.py [-h] [--config_save_path CONFIG_SAVE_PATH]
                            [--output_save_path OUTPUT_SAVE_PATH]
                            [--graph_save_path GRAPH_SAVE_PATH]
                            [--do_not_run | --only_run] [--do_not_average]
                            [--personal] [--random_seed_min RANDOM_SEED_MIN]
                            [--random_seed_max RANDOM_SEED_MAX]
                            [--remove_both_visuals]
                            config_path code_path amount

positional arguments:
  config_path           the configuration file for the experiment to be run
  code_path             where the code is to run the experiment
  amount                how many experiments to run (specify 0 to just average
                        CSVs and create graphs without generating config files
                        or running experiments)

optional arguments:
  -h, --help            show this help message and exit
  --config_save_path CONFIG_SAVE_PATH
                        where to save the generated config files
  --output_save_path OUTPUT_SAVE_PATH
                        where to save the generated output
  --graph_save_path GRAPH_SAVE_PATH
                        where to save the generated graph files
  --do_not_run          include to only generate the config files and command
                        file, not run them
  --only_run            include to only run the config files, not generate
                        them
  --do_not_average      include to not average the CSVs
  --personal            include if running parallel on a personal computer
                        (otherwise runs supercomputer commands)
  --random_seed_min RANDOM_SEED_MIN
                        the minimum random seed number
  --random_seed_max RANDOM_SEED_MAX
                        the maximum random seed number
  --remove_both_visuals
                        include to remove the loop function visualization (in
                        addition to the argos visualization)


So my pbs script is currently


#!/bin/bash -l
#PBS -l walltime=0:15:00,nodes=5:ppn=8,pmem=1000mb
#PBS -m abe
#PBS -M lowma016@umn.edu
module load python3
cd sierra
python3 experiment_runner.py "Sample XML Files/new-single-source-test.argos" ~/fordycaResearch/fordyca 5 --config_save_path ~/sierra_config_test_files --output_save_path ~/sierra_output_test_files


Okay, on my second try I'm going to test doing 10.
#!/bin/bash -l
#PBS -l walltime=0:15:00,nodes=10:ppn=8,pmem=1000mb
#PBS -m abe
#PBS -M lowma016@umn.edu
module load python3
cd sierra
python3 experiment_runner.py "Sample XML Files/new-single-source-test.argos" ~/fordycaResearch/fordyca 10 --config_save_path ~/sierra_config_test_files --output_save_path ~/sierra_output_test_files

I got weird errors regarding a character that was out of bounds. If that happens, just log out and log back in again.

Got back the message "You must specify ppn=24 when requesting 10 or more nodes.", so I'm setting it back to 5 nodes, but keeping it running 10 experiments.
#!/bin/bash -l
#PBS -l walltime=0:15:00,nodes=5:ppn=8,pmem=1000mb
#PBS -m abe
#PBS -M lowma016@umn.edu
module load python3
cd sierra
python3 experiment_runner.py "Sample XML Files/new-single-source-test.argos" ~/fordycaResearch/fordyca 10 --config_save_path ~/sierra_config_test_files --output_save_path ~/sierra_output_test_files
'''

'''
6/27/2018

Finally got it to run and average CSVs on MSI about a week ago, so here's the .pbs file that actually ran it:

#!/bin/bash -l
#PBS -l walltime=0:15:00,nodes=5:ppn=8,pmem=1000mb
#PBS -m abe
#PBS -M lowma016@umn.edu

# Script to get Argos to work
source /home/gini/shared/swarm/bin/build-env-setup.sh

# Load python
module load python3

# From MSI: transfers all of the loaded modules to the nodes
export PARALLEL="--workdir . --env PATH --env LD_LIBRARY_PATH --env LOADEDMODULES --env _LMFILES_ --env MODULE_VERSION --env MODULEPATH --env MODULEVERSION_STACK --env MODULESHOME --env OMP_DYNAMICS --env OMP_MAX_ACTIVE_LEVELS --env OMP_NESTED --env OMP_NUM_THREADS --env OMP_SCHEDULE --env OMP_STACKSIZE --env OMP_THREAD_LIMIT --env OMP_WAIT_POLICY"
# Actual commands to run
cd sierra
python3 experiment_runner.py "Sample XML Files/new-single-source-test.argos" ~/fordycaResearch/fordyca 10 --config_save_path ~/sierra_config_test_files --output_save_path ~/sierra_output_test_files

Here are the things that are next to do:
    make it so that paths can have IDs instead of just tags, and that works in the path
    add in the ability to change tags
    update the README to explain the difference between strict, loose, and loose-strict paths
'''

'''
7/11/2018
So I don't know why I decided to go with loose strict paths for finding elements instead of just being completely loose again,
...like I was for attributes.
Now I'm trying to set the tag of a certain element, and I don't know if that element should be specified with a loose strict path or a loose one.
Was there some reason I couldn't do loose paths with elements?
Yes, I think it was because at the second level there were two elements with the same name and inner structure.
Nope, looking at it, that's not quite right.
It's because I had visualization tag at the bottom (second layer) that I wanted to delete,
...and there was a visualization tag (3rd layer) at the top that I wanted to keep.
So even though they had different layers, I couldn't specify which one I wanted.

Talked to John about it, and he said to keep it the way it is.
That is, keep it doing the loose search for attributes and the loose strict search for elements.
So, I'll also be doing loose strict searches when editing element tags.

Alright, that's done.
So, I've made all the searched work with IDs as well as tags, and you can now change tags.
All that's left is updating the README.
'''
