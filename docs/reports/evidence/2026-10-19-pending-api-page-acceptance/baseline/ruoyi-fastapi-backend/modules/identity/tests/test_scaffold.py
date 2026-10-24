"""Scaffold smoke test for modules.identity."""

import modules.identity.ports as identity_ports


def test_identity_scaffold_importable() -> None:
    assert identity_ports is not None
