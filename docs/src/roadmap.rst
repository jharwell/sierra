.. _ln-sierra-roadmap:

===================
Development Roadmap
===================

This page shows a brief overview of some of the ways I think SIERRA could be
improved. Big picture stuff, not "add more unit tests".

Supporting ROS2
===============

This would require adding several new platform plugin (one for each simulator
that SIERRA supports that supports ROS1, and a new ROS2 real robot
plugin). Since ROS2 still supports XML, this should actually be a fairly
self-contained improvement.

Supporting WeBots
=================

This would require adding a new platform plugin. Should be a fairly
self-contained improvement.

Supporting NetLogo
==================

This would require adding a new platform plugin. I *think* netlogo can take in
XML, so this should be a fairly self-contained improvement. netlogo handles
parallel experimental runs, so that might require some additional configuration,
since none of the currently supported platforms do that.

Adding this would also make SIERRA more appealing/using to researchers outside
of robotics.

Supporting multiple types of experiment input files (not just XML)
==================================================================

This is a fairly involved change, as it affects the SIERRA core. One way I
*cannot* do this is to define yet another plain text format for template inputs
files and say "to use SIERRA you have to use this format". That makes it easier
for me as a developer, but will turn off 90% of people who want a nice plug and
play approach to automating their research.

There are a couple of ways of doing this which might work:

Option 1
--------

Finding an AST tool or stitching a few together to make a toolchain which can
parse to and from arbitrary plain text formats and replace the XML experimental
definition class. All batch criteria and variables would have to be rewritten to
express their changes, additions, or removals from the template input file in
terms of operations on this AST.  Pandoc might be a good starting point, but it
does not support XML out of the box. You would have to do XML -> html with xlst,
and then do html -> whatever with pandoc. No idea if this would be a viable
toolchain which could support pretty much any simulator/platform.

Pros: Makes it easier for SIERRA to support any plain text input format the AST
tool supports.

Cons: Expressing things in terms of operations on an AST instead of changes to a
textual input file is likely to be more confusing and difficult for users as
they create new variables. This change would not be backwards compatible.

Option 2
--------

Keep using XML as the language for the template input files that SIERRA
processes. To support other formats needed by a given simulator or platform,
define a translation layer/engine which takes in XML and outputs the desired
format, or reads it in and transforms it to XML for SIERRA to manipulate.

Pros: Keeps the SIERRA core mostly the same. Reduces the type
restrictions on template input files to "plain text" rather than
strictly XML. Would be backwards compatible.

Cons: Difficult to translate to/from XML/other plaintext formats. xlst
can output plain text from XML, or read plain text and convert it to
XML, but you need to define a schema for how to do that, which may be
very non-trivial. This would make the process of defining platform
plugins for non-XML inputs/outputs much trickier. From SIERRA's
perspective, the changes would be relatively minor.

Option 3
--------

Reworking the SIERRA core to support a set of types of experimental
definitions which would be implemented as plugins: you would have an
XMLExpDef, PythonExpDef, etc. The type of experiment definition and
therefore the type of the template input file could be inferred from
the contents of ``--template-input-file``, or specified on the
cmdline.

Pros: SIERRA core would remain relatively easier to understand, and
this paradigm is in line with SIERRA's plugin philosophy. Would be
backwards compatible.

Cons: You would need multiple versions of a batch criteria or variable
if you wanted that particular criteria to work across platforms which
did not all support XML. You could get around this with a base class
for a given batch criteria/variable which implemented everything but
the actual generation of changes/additions/removals to the
experimental definition, and just have adapter classes for each type
of experimental definition you wanted to be able to use that batch
criteria with. However, there will probably still be cases which would
result in lots of code duplication.
