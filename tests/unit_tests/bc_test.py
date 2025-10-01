#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import sys

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.plugins.engine.argos.variables import population_size
from sierra.core import types, cmdline
from sierra import main


def test_univar_argos():
    args = [
        "sierra-cli",
        "--sierra-root=/tmp/sierra",
        "--engine=engine.argos",
        "--project=projects.sample_argos",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/argos/template.argos",
        "--scenario=HighBlockCount.10x10x2",
        "--controller=foraging.footbot_foraging",
        "--batch-criteria=population_size.Log16",
        "--physics-n-engines=1",
        "--pipeline",
        "1",
        "--exp-overwrite",
    ]

    cmdopts = {
        "project": "projects.sample_argos",
        "engine": "engine.argos",
        "pipeline": [1],
        "expdef": "expdef.xml",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_argos/foraging.footbot_foraging/HighBlockCount.10x10x2/template-population_size.Log16/exp-inputs/"
        ),
        app.args,
        "HighBlockCount.10x10x2",
    )

    assert len(criteria.gen_attr_changelist()) == 5
    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 5
    assert dirnames[0] == "c1-exp0"
    assert dirnames[4] == "c1-exp4"

    app()

    populations = criteria.populations(cmdopts)

    assert populations == [1, 2, 4, 8, 16]

    assert criteria.n_exp() == 5


# 2025-07-22 [JRH]: Use jsonsim here in addition because it has batch criteria
# which contain more than 1 thing in their attr change set.
def test_univar_jsonsim():
    args = [
        "sierra-cli",
        "--sierra-root=/tmp/sierra",
        "--engine=plugins.jsonsim",
        "--project=projects.sample_jsonsim",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/jsonsim/template.argos",
        "--scenario=scenario1",
        "--controller=default.default",
        "--batch-criteria=fuel.1.10.C5",
        "--jsonsim-path=sierra-sample-project/plugins/jsonsim/jsonsim.py",
        "--pipeline",
        "1",
        "--exp-overwrite",
    ]

    cmdopts = {
        "project": "projects.sample_jsonsim",
        "engine": "plugins.jsonsim",
        "pipeline": [1],
        "expdef": "expdef.json",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_jsonsim/default.default/scenario2/template-fuel.1.10.C5/exp-inputs/"
        ),
        app.args,
        "scenario1",
    )

    assert len(criteria.gen_attr_changelist()) == 5
    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 5
    assert dirnames[0] == "c1-exp0"
    assert dirnames[4] == "c1-exp4"

    assert len(criteria.gen_attr_changelist()[0]) == 2
    assert len(criteria.gen_attr_changelist()[4]) == 2


def test_bivar_argos():
    args = [
        "sierra-cli",
        "--sierra-root=/tmp/sierra",
        "--engine=engine.argos",
        "--project=projects.sample_argos",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/argos/template.argos",
        "--scenario=HighBlockCount.100x100x2",
        "--controller=foraging.footbot_foraging",
        "--batch-criteria",
        "population_size.Log16",
        "max_speed.1.9.C4",
        "--physics-n-engines=1",
        "--exp-overwrite",
        "--pipeline",
        "1",
    ]

    cmdopts = {
        "project": "projects.sample_argos",
        "engine": "engine.argos",
        "scenario": "HighBlockCount.10x10x2",
        "pipeline": [1],
        "expdef": "expdef.xml",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_argos/foraging.footbot_foraging/HighBlockCount.100x100x2/template-population_size.Log16+max_speed.1.9.C4/exp-inputs"
        ),
        app.args,
        "HighBlockCount.100x100x2",
    )
    assert len(criteria.gen_attr_changelist()) == 20

    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 20
    assert dirnames[0] == "c1-exp0+c2-exp0"
    assert dirnames[19] == "c1-exp4+c2-exp3"

    app()

    populations = criteria.populations(cmdopts)

    assert len(populations) == 5
    assert len(populations[0]) == 4
    assert len(populations[4]) == 4

    assert criteria.n_exp() == 20
