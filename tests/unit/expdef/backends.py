#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Backend adapters for the expdef conformance suite.

Everything that varies between the XML / JSON / YAML expdef plugins is captured
here, in one small ``Backend`` per plugin. The conformance suite in
``conformance_test.py`` is written once against the abstract ``ExpDef`` interface and
runs against every backend registered in ``ALL_BACKENDS``.
"""

# Core packages
import dataclasses
import pathlib
import typing as tp

# Project packages
from sierra.plugins.expdef.xml import plugin as xml_plugin
from sierra.plugins.expdef.json import plugin as json_plugin
from sierra.plugins.expdef.yaml import plugin as yaml_plugin


@dataclasses.dataclass(frozen=True)
class Backend:
    """Describes one expdef backend to the conformance suite.

    The suite only ever touches the abstract ``ExpDef`` interface; this adapter
    supplies the backend-specific *literals* the abstract tests need:
    constructor, on-disk document bodies, path syntax, and the concrete values
    the documents are known to contain.
    """

    #: Human-readable id; becomes the pytest parametrize id (e.g. "xml").
    name: str

    #: File extension for the on-disk temp document, including dot.
    ext: str

    #: Called as ``ctor(path)`` -> loaded ExpDef. Hides the fact that xml uses
    #: a positional arg while json/yaml use ``input_fpath=``.
    ctor: tp.Callable[[pathlib.Path], tp.Any]

    # Document bodies written to a temp file per test.
    doc_basic: str
    doc_nested: str

    # Path expressions (backend-specific syntax).
    p_app: str
    p_root: str
    p_nested: str
    p_nested_parent: str
    p_missing: str
    p_db: str
    p_db_parent: str
    p_db_child: str

    # Expected concrete values (the type-fidelity contract).
    port_value: tp.Any
    debug_value: tp.Any
    changed_int_value: tp.Any

    # Capability flag: conformance tests skip element_change where unsupported.
    # (Scalar-array and flatten behavior is backend-shaped and lives in the
    # per-backend ``*_quirks_test.py`` files, so it needs no conformance gate.)
    supports_element_change: bool


_JSON_BASIC = """{
  "app": {"name": "MyApp", "port": 8080, "debug": false},
  "database": {"host": "localhost"}
}"""

_JSON_NESTED = """{
  "app": {"config": {"level1": {"level2": {"level3": {"value": "deep"}}}}}
}"""

_YAML_BASIC = """
app:
  name: MyApp
  port: 8080
  debug: false
database:
  host: localhost
"""

_YAML_NESTED = """
app:
  config:
    level1:
      level2:
        level3:
          value: deep
"""

_XML_BASIC = """<?xml version="1.0"?>
<root>
  <app name="MyApp" port="8080" debug="false"/>
  <database host="localhost"/>
</root>"""

_XML_NESTED = """<?xml version="1.0"?>
<root>
  <app><config><level1><level2><level3 value="deep"/></level2></level1></config></app>
</root>"""


ALL_BACKENDS: list["Backend"] = [
    Backend(
        name="xml",
        ext=".xml",
        ctor=lambda p: xml_plugin.ExpDef(p),
        doc_basic=_XML_BASIC,
        doc_nested=_XML_NESTED,
        p_app="app",
        p_root=".",
        p_nested="app/config/level1/level2/level3",
        p_nested_parent="app/config/level1/level2",
        p_missing="nonexistent/path",
        p_db_parent=".",
        p_db_child="database",
        p_db=".//database",
        port_value="8080",
        debug_value="false",
        changed_int_value="42",
        supports_element_change=True,
    ),
    Backend(
        name="json",
        ext=".json",
        ctor=lambda p: json_plugin.ExpDef(input_fpath=p),
        doc_basic=_JSON_BASIC,
        doc_nested=_JSON_NESTED,
        p_app="$.app",
        p_root="$",
        p_nested="$.app.config.level1.level2.level3",
        p_nested_parent="$.app.config.level1.level2",
        p_missing="$.nonexistent.path",
        p_db_parent="$",
        p_db_child="database",
        p_db="$.database",
        port_value=8080,
        debug_value=False,
        changed_int_value=42,
        supports_element_change=False,
    ),
    Backend(
        name="yaml",
        ext=".yaml",
        ctor=lambda p: yaml_plugin.ExpDef(input_fpath=p),
        doc_basic=_YAML_BASIC,
        doc_nested=_YAML_NESTED,
        p_app="app",
        p_root="/",
        p_nested="/app/config/level1/level2/level3",
        p_nested_parent="/app/config/level1/level2",
        p_missing="nonexistent/path",
        p_db="database",
        p_db_parent="",
        p_db_child="database",
        port_value=8080,
        debug_value=False,
        changed_int_value=42,
        supports_element_change=True,
    ),
]
