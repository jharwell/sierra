#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""A typed SIERRA command builder.

Builds an argv ``list[str]`` directly, so:
* arguments with spaces survive (``.split()`` mangled them),
* flags are set/overridden/removed by name, not by string editing,
* the rendered command is diffable and inspectable in failures.
"""

# Core packages
import dataclasses
import typing as tp


@dataclasses.dataclass
class SierraCommand:
    """Accumulates argv for a SIERRA invocation.

    Start from an engine base command (already an argv list) and layer
    per-test flags on top by name.
    """

    _argv: tp.List[str]
    _flags: tp.Dict[str, tp.Optional[str]] = dataclasses.field(default_factory=dict)
    #: Flags whose value is a space-separated list rendered as ``--flag a b c``
    #: (SIERRA's ``nargs='+'`` style), e.g. ``--pipeline 1 2 3`` or
    #: ``--proc proc.statistics proc.collate``. Kept separate from ``_flags`` so
    #: render() knows to emit ``--flag v1 v2`` rather than ``--flag=v1 v2``.
    _multi: tp.Dict[str, tp.Tuple[str, ...]] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_base(cls, base_argv: tp.Sequence[str]) -> "SierraCommand":
        return cls(_argv=list(base_argv))

    def copy(self) -> "SierraCommand":
        """Fork an independent builder from this one.

        The builder mutates in place (``set``/``pipeline``/``remove`` all return
        ``self``), which is convenient for linear construction but wrong when
        several *variant* commands share a common base: without a copy, flags
        from one variant leak into the next. ``copy`` gives each variant its own
        flag dict so ``base.copy().set(...)`` never disturbs ``base``.
        """
        return SierraCommand(
            _argv=list(self._argv),
            _flags=dict(self._flags),
            _multi=dict(self._multi),
        )

    def set(self, flag: str, value: tp.Optional[str] = None) -> "SierraCommand":
        """Set/override ``--flag`` or ``--flag=value`` by name."""
        self._flags[flag] = value
        self._multi.pop(flag, None)
        return self

    def set_multi(self, flag: str, values: tp.Sequence[str]) -> "SierraCommand":
        """Set a multi-value (``nargs='+'``) flag, rendered ``--flag a b c``.

        For SIERRA options that take a space-separated list rather than a single
        ``=value`` (e.g. ``--proc proc.statistics proc.collate``). Overrides any
        prior single/multi setting of the same flag.
        """
        self._multi[flag] = tuple(values)
        self._flags.pop(flag, None)
        return self

    def remove(self, flag: str) -> "SierraCommand":
        """Drop a flag entirely."""
        self._flags[flag] = _REMOVED
        self._multi.pop(flag, None)
        return self

    def pipeline(self, *stages: int) -> "SierraCommand":
        return self.set_multi("--pipeline", [str(s) for s in stages])

    def render(self) -> tp.List[str]:
        """Produce the final argv, base flags overlaid by explicit ones."""
        out = list(self._argv)

        # Single-value / boolean / removed flags.
        for flag, value in self._flags.items():
            out = [a for a in out if not a.split("=", 1)[0] == flag]
            if value is _REMOVED:
                continue
            if value is None:
                out.append(flag)
            else:
                out.append(f"{flag}={value}")

        # Multi-value (nargs='+') flags: --flag v1 v2 v3. Also strip any
        # ``--flag=...`` form the base cmd may have carried.
        for flag, values in self._multi.items():
            out = [a for a in out if not a.split("=", 1)[0] == flag]
            out.extend([flag, *values])

        return out


_REMOVED = object()
