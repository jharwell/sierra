#!/usr/bin/env python3
"""Regenerate every figure referenced by docs/src/plugins/prod/graphs.rst.

Runs the SIERRA sample projects for BOTH the matplotlib and bokeh backends and
collects the results into a ready-to-drop-in ``figures/`` tree whose paths match
graphs.rst.

WHY THIS SCRIPT EXISTS (bokeh single-version constraint)
--------------------------------------------------------
Bokeh embeds a serialized model into each standalone HTML blob. When a browser
renders a page (a Sphinx doc page) containing several such blobs, it loads
BokehJS exactly ONCE -- the version demanded by the FIRST blob it encounters --
and only blobs whose serialization matches that BokehJS version render; the rest
silently blank out. So every .html figure that can land on the SAME doc page MUST
be produced by the SAME bokeh version. The only reliable guarantee is to
regenerate them all in one pass with one pinned environment (see --bokeh-version).
The matplotlib PNGs have no such constraint; we regenerate them in the same pass
anyway so both backends come from identical data + sierra version, with no drift
between the static and interactive tabs. Stages 1-3 (generate/run/process+collate)
are backend-agnostic, so they run ONCE per project (with the first backend); each
subsequent backend re-runs stage 4 ONLY against the same --sierra-root, reusing
the collated data instead of re-simulating.

ON-DISK LAYOUT (from sierra core batchroot.py)
----------------------------------------------
Batch root:
  <sierra_root>/<project>/<controller>/<scenario>/<template_stem>-<criteria>
Under it (PathSet.from_root):
  graphs/                 <- intra-experiment graph root
  graphs/<per-exp-dir>/   <- one dir per experiment (RST examples show ONE exp)
  graphs/inter-exp/       <- collated inter-experiment graphs
Each graph is written as <dest>.png (matplotlib) or <dest>.html (bokeh). This
script imports sierra.core.batchroot directly to resolve those paths, so it never
duplicates the path formula.

OUTPUT: a drop-in figures/ tree (ZERO renaming)
-----------------------------------------------
The collector does NOT rename anything. It copies each graphs directory WHOLESALE
into a subdir that mirrors the run:
    figures/<project>/intra[-<stats>]/<dest>.{png,html}   (per-exp graphs)
    figures/<project>/inter/<dest>.{png,html}             (collated graphs)
Disambiguation is the subdir PATH (project + scope + stats), never the filename.
After a run:  cp -r <staging>/figures docs/src/plugins/prod/
"""

import argparse
import dataclasses
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import typing as tp


# --------------------------------------------------------------------------
# Pretty output
# --------------------------------------------------------------------------
def say(msg: str) -> None:
    print(f"\033[1;34m==>\033[0m {msg}")


def warn(msg: str) -> None:
    print(f"\033[1;33m[warn]\033[0m {msg}", file=sys.stderr)


def die(msg: str) -> tp.NoReturn:
    print(f"\033[1;31m[fatal]\033[0m {msg}", file=sys.stderr)
    raise SystemExit(1)


# --------------------------------------------------------------------------
# Project descriptions -- data, not repeated code.
# --------------------------------------------------------------------------
@dataclasses.dataclass
class Project:
    """One sample project to regenerate, plus how to invoke and collect it."""

    name: str  # --only selector, and figures/<name>/ prefix
    controller: str
    engine: str
    project: str  # sierra --project value
    scenario: str
    template: str  # basename under <sample_root>/exp/<...>
    criteria: str
    # Extra flags common to every backend/stats invocation for this project.
    extra_flags: tp.List[str] = dataclasses.field(default_factory=list)
    # Extra environment variables the sierra subprocess needs, as a list of
    # (name, value-suffix) pairs. The suffix is appended to any existing value
    # of that var (':'-joined, PATH-style), so a pre-set value is preserved.
    # {sample_root} in the suffix is expanded. ARGoS needs ARGOS_PLUGIN_PATH to
    # point at the compiled controller/loop-function libraries.
    env_append: tp.List[tp.Tuple[str, str]] = dataclasses.field(default_factory=list)
    # ARGoS varies --spread and tags the intra subdir with it; other projects
    # use a single (None) variant collected into plain intra/.
    stats_spread: tp.List[tp.Optional[str]] = dataclasses.field(
        default_factory=lambda: [None]
    )
    stats_center: tp.List[tp.Optional[str]] = dataclasses.field(
        default_factory=lambda: "mean"
    )

    # Collect the collated inter-exp graphs only on this stats value (ARGoS shows
    # them once, not per-stats). None => collect on the single/first variant.
    inter_on_stats: tp.Optional[str] = None
    expect_fail: bool = False  # pending config: never aborts the regen

    def template_path(self, sample_root: pathlib.Path) -> pathlib.Path:
        return sample_root / "exp" / self.name / self.template

    def sierra_root(self, base: str, stats: tp.Optional[str]) -> str:
        # ARGoS uses per-stats roots (<base>-none / <base>-conf95); single-variant
        # projects use <base>-<name>.
        suffix = stats if stats is not None else self.name
        return f"{base}-{suffix}"

    def build_env(self, sample_root: pathlib.Path) -> tp.Optional[tp.Dict[str, str]]:
        """Return the subprocess environment, or None if unchanged from parent.

        Each (name, suffix) in env_append is appended PATH-style to the current
        value of that variable, preserving anything already set.
        """
        if not self.env_append:
            return None
        env = dict(os.environ)
        for name, suffix in self.env_append:
            suffix = suffix.format(sample_root=sample_root)
            existing = env.get(name, "")
            env[name] = f"{existing}:{suffix}" if existing else suffix
        return env


def build_projects(sample_root: pathlib.Path) -> tp.List[Project]:
    return [
        Project(
            name="argos",
            controller="foraging.footbot_foraging",
            engine="engine.argos",
            project="projects.sample_argos",
            scenario="LowBlockCount.10x10x2",
            template="template.argos",
            criteria="population_size.Linear5.C5",
            extra_flags=[
                "--exp-setup=exp_setup.T1000.K5",
                "--physics-n-engines=1",
                "--with-robot-leds",
                "--with-robot-rab",
                "--exp-n-datapoints-factor=0.1",
            ],
            stats_center=["mean", "median"],
            spread=["bw", "conf95"],
            inter_on_stats="none",
            env_append=[("ARGOS_PLUGIN_PATH", "{sample_root}/argos/build")],
        ),
        Project(
            name="yamlsim",
            controller="default.default",
            engine="plugins.yamlsim",
            project="projects.sample_yamlsim",
            scenario="scenario1",
            template="template.yaml",
            criteria="noise_floor.1.9.C5",
            extra_flags=[
                "--expdef=expdef.yaml",
                f"--yamlsim-path={sample_root}/plugins/yamlsim/yamlsim.py",
                "--proc",
                "proc.statistics",
                "proc.collate",
            ],
        ),
        Project(
            name="jsonsim",
            controller="signal.lowpass",
            engine="plugins.jsonsim",
            project="projects.sample_jsonsim",
            scenario="cleanroom",
            template="template.json",
            criteria="max_speed.1.9.C5",
            extra_flags=[
                "--expdef=expdef.json",
                f"--jsonsim-path={sample_root}/plugins/jsonsim/jsonsim.py",
                "--proc",
                "proc.statistics",
                "proc.collate",
            ],
        ),
    ]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
class Regen:
    BACKENDS = ("matplotlib", "bokeh")

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.figdir = pathlib.Path(args.fig_staging) / "figures"
        self.failed: tp.List[str] = []
        self.missing: tp.List[str] = []
        # sierra.core.batchroot -- imported once, used to resolve graph roots.
        try:
            from sierra.core import batchroot
        except Exception as e:  # pragma: no cover - surfaced to the user
            die(
                f"could not import sierra.core.batchroot ({e}). "
                "Is the SIERRA env active?"
            )
        self._batchroot = batchroot

    # -- stage selection ---------------------------------------------------
    def pipeline_stages(self, backend: str) -> tp.List[str]:
        """Stages 1-3 are backend-agnostic; only stage 4 renders graphs.

        Full pipeline for the first backend, stage 4 only for the rest.
        """
        return ["1", "2", "3", "4"] if backend == self.BACKENDS[0] else ["4"]

    # -- path resolution via the real module -------------------------------
    def graph_roots(
        self, proj: Project, sierra_root: str
    ) -> tp.Tuple[pathlib.Path, pathlib.Path]:
        ns = argparse.Namespace(
            sierra_root=sierra_root,
            project=proj.project,
            controller=proj.controller,
            scenario=proj.scenario,
            expdef_template=str(proj.template_path(self.args.sample_root)),
            batch_criteria=[proj.criteria],
        )
        pathset = self._batchroot.from_cmdline(ns)
        return pathset.graph_root, pathset.graph_interexp_root

    # -- bokeh guard -------------------------------------------------------
    def check_bokeh(self) -> None:
        want = self.args.bokeh_version
        if not want:
            return
        try:
            import bokeh

            have = bokeh.__version__
        except Exception:
            die(f"--bokeh-version {want} requested but bokeh not importable")
        if have != want:
            die(
                f"bokeh mismatch: active={have} required={want}; all .html on a "
                "page must share one version. Refusing."
            )
        say(f"bokeh version pinned OK: {have}")

    # -- one sierra invocation --------------------------------------------
    def run(
        self,
        expect_fail: bool,
        label: str,
        cmd: tp.List[str],
        env: tp.Optional[tp.Dict[str, str]] = None,
    ) -> None:
        say(label)
        if self.args.dry_run:
            # Show only the vars this project actually adds, as a pasteable prefix.
            prefix = ""
            if env is not None:
                added = _env_diff(env)
                prefix = "".join(f"{k}={shlex.quote(v)} " for k, v in added)
            print("    " + prefix + shlex.join(cmd))
            return
        proc = subprocess.run(cmd, env=env)
        if proc.returncode == 0:
            return
        if expect_fail:
            warn(
                f"{label} FAILED (rc={proc.returncode}) -- expected until "
                "config/data added"
            )
            return
        warn(f"{label} FAILED (rc={proc.returncode})")
        self.failed.append(label)
        if not self.args.keep_going:
            die("aborting on failed required run (use --keep-going)")

    # -- per-exp dir selection --------------------------------------------
    def perexp_dir(self, graph_root: pathlib.Path) -> tp.Optional[pathlib.Path]:
        if not graph_root.is_dir():
            return None
        # Exclude the collated inter-exp dir, which also matches an '*exp*' glob.
        dirs = sorted(
            (
                d
                for d in graph_root.glob(self.args.perexp_glob)
                if d.is_dir() and d.name != "inter-exp"
            ),
            key=_natural_key,
        )
        if not dirs:
            return None
        if self.args.exp_index == "last":
            return dirs[-1]
        for d in dirs:
            if d.name.endswith(f"exp{self.args.exp_index}"):
                return d
        return None

    # -- wholesale collect (zero renaming) --------------------------------
    def collect_dir(self, src: tp.Optional[pathlib.Path], sub: str, label: str) -> None:
        dst = self.figdir / sub
        if self.args.dry_run:
            print(f"    collect {src}/*.{{png,html}} -> figures/{sub}/")
            return
        if src is None or not src.is_dir():
            self.missing.append(f"{label}  (no source dir: {src or '<unresolved>'})")
            return
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted([*src.glob("*.png"), *src.glob("*.html")]):
            if f.is_file():
                shutil.copy2(f, dst / f.name)
                n += 1
        if n == 0:
            self.missing.append(f"{label}  (source dir empty: {src})")

    # -- build a sierra command for one (project, backend, stats) ----------
    def sierra_cmd(
        self, proj: Project, backend: str, stats: tp.Optional[str], sierra_root: str
    ) -> tp.List[str]:
        cmd = [
            "sierra",
            f"--sierra-root={sierra_root}",
            f"--controller={proj.controller}",
            f"--engine={proj.engine}",
            f"--project={proj.project}",
            "--n-runs=4",
            f"--expdef-template={proj.template_path(self.args.sample_root)}",
            f"--scenario={proj.scenario}",
            *proj.extra_flags,
            "--batch-criteria",
            proj.criteria,
            "--prod",
            "prod.graphs",
            f"--graphs-backend={backend}",
            "--exp-overwrite",
        ]
        if stats is not None:
            cmd.append(f"--spread={stats}")
        cmd += ["--pipeline", *self.pipeline_stages(backend)]
        return cmd

    # -- drive one project -------------------------------------------------
    def do_project(self, proj: Project) -> None:
        env = proj.build_env(self.args.sample_root)
        for stats in proj.stats_spread:
            sierra_root = proj.sierra_root(self.args.sierra_root, stats)
            tag = stats or proj.name
            for backend in self.BACKENDS:
                label = f"{proj.name.upper()}  stats={stats or '-'}  backend={backend}"
                self.run(
                    proj.expect_fail,
                    label,
                    self.sierra_cmd(proj, backend, stats, sierra_root),
                    env=env,
                )

            if not self.args.collect:
                continue

            intra_root, inter_root = self.graph_roots(proj, sierra_root)
            xe = self.perexp_dir(intra_root)
            # ARGoS tags intra with the stats value; single-variant projects don't.
            intra_sub = (
                f"{proj.name}/intra-{stats}"
                if stats is not None
                else f"{proj.name}/intra"
            )
            self.collect_dir(xe, intra_sub, f"{proj.name} intra ({tag})")

            # Collect the collated inter-exp graphs only once. For ARGoS that's
            # the 'none' pass; for single-variant projects it's the only pass.
            collect_inter = proj.inter_on_stats is None or stats == proj.inter_on_stats
            if collect_inter:
                self.collect_dir(inter_root, f"{proj.name}/inter", f"{proj.name} inter")

    # -- top level ---------------------------------------------------------
    def main(self) -> int:
        if not shutil.which("sierra"):
            die("sierra not on PATH -- activate the SIERRA env first")
        self.figdir.mkdir(parents=True, exist_ok=True)
        self.check_bokeh()

        say(f"sierra-root : {self.args.sierra_root}")
        say(f"sample-root : {self.args.sample_root}")
        say(f"figures out : {self.figdir}")
        say(
            f"backends    : {' '.join(self.BACKENDS)}   exp-index: {self.args.exp_index}"
        )
        if self.args.bokeh_version:
            say(f"bokeh pin   : {self.args.bokeh_version}")
        if self.args.dry_run:
            say("MODE        : DRY RUN")

        projects = build_projects(self.args.sample_root)
        for proj in projects:
            if self.args.only and self.args.only != proj.name:
                continue
            self.do_project(proj)

        print()
        if self.args.collect and not self.args.dry_run and self.missing:
            warn("Figures expected but NOT found (collection skipped them):")
            for m in self.missing:
                print(f"    - {m}", file=sys.stderr)
        if self.failed:
            warn("Required runs that FAILED:")
            for f in self.failed:
                print(f"    - {f}", file=sys.stderr)
            return 1

        say("Done.")
        if self.args.collect and not self.args.dry_run:
            print(f"\nDrop-in ready:  {self.figdir}")
            print(f'  cp -r "{self.figdir}" docs/src/plugins/prod/')
            print(
                "All .html in that dir came from this single run => one bokeh "
                "version =>"
            )
            print(
                "no cross-version blank-out. Rebuild ALL .html together if you "
                "rebuild any."
            )
        return 0


def _env_diff(env: tp.Dict[str, str]) -> tp.List[tp.Tuple[str, str]]:
    """Vars in env that differ from os.environ, for a pasteable dry-run prefix."""
    return [(k, v) for k, v in env.items() if os.environ.get(k) != v]


def _natural_key(p: pathlib.Path) -> tp.List[tp.Union[int, str]]:
    """Sort key mimicking `sort -V` for exp0, exp1, ... exp10 ordering."""
    import re

    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.name)]


def parse_args(argv: tp.Optional[tp.List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Regenerate graphs.rst figures from the SIERRA sample projects.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print sierra invocations, don't run or collect",
    )
    ap.add_argument(
        "--only", metavar="NAME", help="run only one project: argos|yamlsim|jsonsim"
    )
    ap.add_argument(
        "--keep-going",
        action="store_true",
        help="don't stop on the first failing required run",
    )
    ap.add_argument(
        "--no-collect",
        dest="collect",
        action="store_false",
        help="run sierra but skip the figures/ collection step",
    )
    ap.add_argument(
        "--sierra-root",
        default=os.environ.get("SIERRA_ROOT", os.path.expanduser("~/test")),
        help="base sierra root; per-group roots derived as "
        "<root>-none/-conf95/-yamlsim/-jsonsim",
    )
    ap.add_argument(
        "--sample-root",
        type=pathlib.Path,
        default=os.environ.get(
            "SAMPLE_ROOT", os.path.expanduser("~/git/thesis/sierra-sample-project")
        ),
        help="sierra-sample-project checkout",
    )
    ap.add_argument(
        "--fig-staging",
        default=os.environ.get("FIG_STAGING", "/tmp/staging"),
        help="where the figures/ tree is assembled",
    )
    ap.add_argument(
        "--bokeh-version",
        default=os.environ.get("BOKEH_VERSION", ""),
        help="if set, refuse to run unless active bokeh matches",
    )
    ap.add_argument(
        "--exp-index",
        default=os.environ.get("EXP_INDEX", "last"),
        help="which experiment's intra graphs to collect " "('last' or an integer)",
    )
    ap.add_argument(
        "--perexp-glob",
        default=os.environ.get("PEREXP_GLOB", "*exp*"),
        help="glob for per-exp graph dirs under graphs/",
    )
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(Regen(parse_args()).main())
