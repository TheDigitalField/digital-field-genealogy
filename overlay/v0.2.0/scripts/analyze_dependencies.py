#!/usr/bin/env python3
"""Report common causes and single-principal impact in a public dependency graph."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    nodes = {item["id"]: item for item in graph["nodes"]}
    impact: dict[str, list[str]] = defaultdict(list)
    for node in graph["nodes"]:
        for principal in node.get("principals", []):
            impact[principal].append(node["id"])

    shared = {
        principal: sorted(affected)
        for principal, affected in impact.items()
        if len(affected) > 1
    }
    missing = sorted({
        principal
        for item in graph["nodes"]
        for principal in item.get("principals", [])
        if principal not in nodes
    })
    report = {
        "schema": "digital-field-common-cause-analysis/v1",
        "status": "passed" if not missing else "failed",
        "node_count": len(nodes),
        "principal_impact": {key: sorted(value) for key, value in sorted(impact.items())},
        "shared_causes": shared,
        "missing_references": missing,
        "claims": graph.get("claims", {}),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

