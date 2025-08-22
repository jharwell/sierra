.. _roadmap:

===================
Development Roadmap
===================

This page shows a brief overview of some of the ways I think SIERRA could be
improved. Big picture stuff, not "add more unit tests".

SIERRA2
=======

SIERRA is beginning to really mature, and so I think it isappropriate to lay out
the improvements needed to go into a 2.0 version. Most of this is
maturing/improving the plugin framework.

Right now there are plugins for engines, execution environments, and storage
media for experimental outputs, which cover stages {1,2} well in terms of ease
of use/adoption. Stages {3,4,5} are plugin-ish, but really not, because they
only provide options for tweaking what is there, not loading entirely new
plugins. The configuration hooks for overriding/extending them are plugin-ish,
but also seem kind of like a band-aid.

So I think an important shift would be to remove usage of all the configuration
hooks (or at least most of them), and replace with plugins, with the idea being
that if a given plugin doesn't work for a given user's desires, they can
copy/modify it so that it works for them and then just put it on SIERRA's plugin
path.

Stage 3
-------

In stage 3, the plugins will be post-processors (probably called ``proc``
plugins). Currently in the core we have:

- Statistics generation

- Imagizing

- Run collation

The first two should be easy to convert to plugins, because their functionality
is clearly optional from a user perspective, and thus not really tied to the
SIERRA core per-se. It's easy to imagine someone who doesn't care about
statistics, because they are only generating videos, or isn't generating images
from .csv files. Run collation is a little trickier, because it *is* tied into
the SIERRA core in that that is how you build .csv files which can be directly
used to generate deliverables in stage 4 for inter-experiment graphs. But again,
someone might not be interested in those types of graphs for whatever reason,
and so wouldn't be interested in collating things.

Stage {4,5}
-----------

In stage 4, the plugins will be deliverable generators (probably called
``deliverable`` plugins). Currently in the core we have:

- Intra/inter experiment graphs

- Models

- Video generation from images

Models are already plugin-based. Graphs would need to be updated to be plugins.
Right now, stage {4,5} are tied to matplotlib, and cannot be easily made to work
using a different engine. Holoviews is a superset of matplotlib; matplotlib is
one selectable backend. Making the switch will make generating static plots, web
plots, etc. seamless. All of the current set of graph types (StackedLine,
Summary, etc.) should be localized to the new ``hv`` plugin.

In addition, the configurability/hooks available in stage {4,5} for specifying
what data goes on what graphs fees a bit clunky, as it was developed mostly for
my thesis/hacked on as needed.. In *theory* you can just slot in whatever
deliverable generation code you want to, but it feels like an afterthought. What
*should* happen is:

- Deliverable generation for stage 4 is defined on a per-plugin basis:
  inter/intra graphs for the ``hv`` plugin, for example.

- Configurability still is via YAML, BUT now you have different files for
  different plugins.

Finally, there need to be several new tutorials for not only how to write
hooks/plugins for stages {4,5}, but also how to *use* what is defined in an
end-user workflow. The current examples don't show *any* of this, and the
question of "How do I use SIERRA to generate what I really care about" isn't
really answered anywhere.

Beyond SIERRA2
==============

Once the 2.0 release is done, that will set the stage for adding more plugins.

Supporting ROS2
---------------

This would require adding several new engine plugin (one for each simulator
that SIERRA supports that supports ROS1, and a new ROS2 real robot
plugin). Since ROS2 still supports XML, this should actually be a fairly
self-contained improvement.

Supporting WeBots
-----------------

This would require adding a new engine plugin. Should be a fairly
self-contained improvement.

Supporting NetLogo
------------------

This would require adding a new engine plugin. I *think* netlogo can take in
XML, so this should be a fairly self-contained improvement. netlogo handles
parallel experimental runs, so that might require some additional configuration,
since none of the currently supported engines do that.

Adding this would also make SIERRA more appealing/using to researchers outside
of robotics.

Expanded Workflows
------------------

It would be useful to be able to evaluate user code computationally, in addition
to whatever scientific/research flavored evaluations. That is, having a workflow
where SIERRA analyzes things like:

- How long sims (really the algorithms/controllers used) took. This would be
  done by treating the stuff in the statistics/exec folder as first-class data
  and operating on it.

- The performance profile of sims (really the algorithms/controllers used) using
  something like vtune, grof, kcachegrind, etc. This would be done by wrapping
  the call to execute given sim on a target engine with whatever is required
  by the profiling tool, and then averaging (if supported by the tool) the data
  in stage 3, and generating some graphs/reports from the data in stage 4
  (hopefully using native faculties the tool provides).

  This raises a nuanced point about plugins: should they be categorical, or
  functional? E.g., for profiling with vtune, should we have ``proc.vtune``,
  ``deliverable.vtune`` plugins in stages 3 and 4 respectively, OR have
  ``vtune.proc`` and ``vtune.deliverable`` plugins. One is more tool/backend
  based, and one is more functional. The same issue will arise with holoviews in
  stages 4/5: ``hv.deliverable`` and ``hv.comparator`` or ``deliverable.hv`` and
  ``comparator.hv``. In the latter case I think it makes more sense to have
  ``hv.X``, because that will make it easier/cleaner to reuse code common to
  usage of hv in stage 4/5. This decision is a long way off, and doesn't really
  matter at this juncture.

- The contributions of each dimension in an N-dim batch criteria to the observed
  performance (i.e., principle component analysis).

- Regression testing: given the cmdline args + a pointer to some blessed
  referenced data, generate a report of what items passed and which failed. This
  should be fairly straightforward, because the blessed data would come from a
  previous experiment, and therefore be packaged in SIERRA's directory structure.

Rewrite in Rust
---------------

Stage1 would greatly benefit from rewriting in rust, because they
don't involve any "exotic" 3rd party libs like pandas/holoviews. Rewriting in
rust would bring a massive speed boost to generating large experiments in
stage1. Rewriting other stages in rust *might* be helpful, but there would be a
limit to the rewrite, because e.g., holoviews would still have to be used. An
interesting programming and architecture challenge, to say the least.
