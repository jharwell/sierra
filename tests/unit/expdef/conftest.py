#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Test setup for the expdef unit tests.

The expdef plugins log at SIERRA's custom TRACE level in their attr/element
mutation paths (e.g. ``logger.trace(...)``). SIERRA installs that level in
``sierra.core.logging.initialize()`` (via ``haggis.logs.add_logging_level``),
which runs during CLI startup -- not when a unit test constructs an ``ExpDef``
directly.

Without this conftest, TRACE registration would depend on some *other* test
module (e.g. bc_test, which builds ``main.SIERRA(...)`` and thereby calls
``initialize()``) running first — a fragile import-order dependency. Making the
setup explicit here keeps it order-independent, so the expdef suite passes in
isolation (``pytest tests/unit/expdef/``) as well as in a full run.
"""

# Core packages
import logging

# 3rd party packages
import pytest


def _trace_registered() -> bool:
    return hasattr(logging.getLoggerClass(), "trace")


@pytest.fixture(autouse=True, scope="session")
def sierra_trace_level():
    """Register SIERRA's TRACE level before any expdef test runs.

    Calls SIERRA's own ``initialize()`` so the tests exercise the real logging
    path. Guarded on ``hasattr(..., "trace")`` so that if the level is already
    installed (e.g. another test module ran first) we don't re-run
    ``coloredlogs.install()`` and disturb pytest's log capture.
    """
    if not _trace_registered():
        from sierra.core import logging as sierra_logging

        # WARNING keeps test output quiet while still installing TRACE.
        sierra_logging.initialize("WARNING")

    yield
