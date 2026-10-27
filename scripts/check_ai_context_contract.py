"""Validate the local draft schemas and shared synthetic fixtures without network access."""

import json
import re
import socket
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1] / "shared" / "ai-context"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check():
    checked = 0
    validators = {}
    for name in ["manifest", "request", "events"]:
        schema = read(ROOT / f"{name}.schema.json")
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema)
        for path in sorted((ROOT / "vectors" / name).glob("*.json")):
            case = read(path)
            assert validators[name].is_valid(case["value"]) == case["valid"], path.name
            checked += 1
    grammar = read(ROOT / "placeholder-grammar.json")
    pattern = re.compile(grammar["wholePattern"])
    reverse = {prefix: kind for kind, prefix in grammar["prefixes"].items()}
    for case in read(ROOT / "vectors" / "placeholders.json")["cases"]:
        match = pattern.fullmatch(case["value"])
        assert bool(match) == case["valid"], case["value"]
        if match:
            assert reverse[match[1]] == case["kind"]
        checked += 1
    streams = read(ROOT / "vectors" / "streams" / "boundaries.json")
    for case in streams["cases"]:
        for frame in case["events"]:
            validators["events"].validate(frame)
        checked += 1
    # Sequence/HTTP expectations are consumed by the application adapters later;
    # schema validity does not establish terminal or authentication semantics.
    assert read(ROOT / "draft.json")["frozen"] is False
    print(
        json.dumps(
            {
                "schemas": 3,
                "fixtures_checked": checked,
                "network": "denied",
                "status": "pass",
            }
        )
    )


if __name__ == "__main__":
    with (
        patch.object(
            socket, "getaddrinfo", side_effect=AssertionError("network forbidden")
        ),
        patch.object(
            socket.socket, "connect", side_effect=AssertionError("network forbidden")
        ),
    ):
        check()
