.. _roadmap:

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

Better Deliverable Generation Backend + Configurability
=======================================================

Right now, stage {4,5} are tied to matplotlib, and cannot be easily made to work
using a different engine. Holoviews is a superset of matplotlib; matplotlib is
one selectable backend. Making the switch will make generating static plots, web
plots, etc. seamless. There should be a core set of graph types (StackedLine,
Summary, etc.) which are defined by each plugin; custom plugins can choose not
to define/implement those graphs, but then you get an error if configuration
tells SIERRA to generate a type of graph that the selected plugin doesn't
define.

In addition, the configurability/hooks available in stage {4,5} for specifying
what data goes on what graphs fees a bit clunky, as it was developed mostly for
my thesis/hacked on as needed.. In *theory* you can just slot in whatever
deliverable generation code you want to, but it feels like an afterthought. What
*should* happen is:

- Deliverable generation for stage 4 is broken into two plugins: inter/intra,
  which (well, or maybe one plugin, depending), and treated as a "first class"
  SIERRA plugin.

- Configurability still is via YAML, BUT now you have different sections for
  different plugins (if you want), maybe different categories for different
  plugins, etc.

Finally, there need to be several new tutorials for not only how to write
hooks/plugins for stages {4,5}, but also how to *use* what is defined in an
end-user workflow. The current examples don't show *any* of this, and the
question of "How do I use SIERRA to generate what I really care about" isn't
really answered anywhere.
