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
'''
