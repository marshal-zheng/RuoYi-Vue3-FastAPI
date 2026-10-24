"""Scaffold smoke test for modules.project."""

import modules.project.ports as project_ports


def test_project_scaffold_importable() -> None:
    assert project_ports is not None
