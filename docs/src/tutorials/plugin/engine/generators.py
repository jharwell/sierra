import pathlib

from sierra.core.experiment import definition
from sierra.core import types
from sierra.core.experiment import spec
from sierra.core import plugin_manager as pm


def for_all_exp(spec: spec.ExperimentSpec,
                controller: str,
                cmdopts: types.Cmdopts,
                expdef_template_fpath: pathlib.Path) -> definition.BaseExpDef:
    """
    Create an experiment definition from the
    ``--expdef-template`` and generate expdef changes to input files
    that are common to all experiments on the engine. All projects
    using this engine should derive from this class for `their`
    project-specific changes for the engine.

    Arguments:

        spec: The spec for the experimental run.

        controller: The controller used for the experiment, as passed
                    via ``--controller``.

        exp_def_template_fpath: The path to ``--expdef-template``.
    """
    # Only needed if your engine supports multiple input formats. Otherwise
    # just hardcode the string identifying the root element.
    fmt = pm.pipeline.get_plugin_module(cmdopts["expdef"])

    # Assuming engine takes a single file as input
    wr_config = definition.WriterConfig([{"src_parent": None,
                                          "src_tag": fmt.root_querypath(),
                                          "opath_leaf": ".myextension",
                                          "new_children": None,
                                          "new_children_parent": None,
                                          "rename_to": None
                                          }])
    module = pm.pipeline.get_plugin_module(cmdopts["expdef"])

    expdef = module.ExpDef(input_fpath=expdef_template_fpath,
                           write_config=wr_config)

    # Optional, only needed if your engine supports nested
    # configuration files.
    expdef.flatten(["pathstring1", "pathstring2"])

    return expdef


def for_single_exp_run(
        exp_def: definition.BaseExpDef,
        run_num: int,
        run_output_path: pathlib.Path,
        launch_stem_path: pathlib.Path,
        random_seed: int,
        cmdopts: types.Cmdopts) -> definition.BaseExpDef:
    """
    Generate expdef changes unique to a experimental run within an
    experiment for the matrix engine.

    Arguments:
        exp_def: The experiment definition after ``--engine`` changes
        common to all experiments have been made.

        run_num: The run # in the experiment.

        run_output_path: Path to run output directory within
                         experiment root (i.e., a leaf).

        launch_stem_path: Path to launch file in the input directory
                          for the experimental run, sans extension
                          or other modifications that the engine
                          can impose.

        random_seed: The random seed for the run.

        cmdopts: Dictionary containing parsed cmdline options.
    """
    pass
