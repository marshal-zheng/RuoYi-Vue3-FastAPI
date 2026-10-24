"""Scaffold smoke test for modules.device."""

import modules.device.ports as device_ports


def test_device_scaffold_importable() -> None:
    assert device_ports is not None
