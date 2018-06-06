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
path to xml path to argos files path to xml storage path to csvs and graphs
'''
