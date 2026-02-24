"""Scaffold smoke test for modules.codegen."""

import modules.codegen.ports as codegen_ports


def test_codegen_scaffold_importable() -> None:
    assert codegen_ports is not None
