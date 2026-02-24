"""Scaffold smoke test for modules.protocol."""

import modules.protocol.ports as protocol_ports


def test_protocol_scaffold_importable() -> None:
    assert protocol_ports is not None
