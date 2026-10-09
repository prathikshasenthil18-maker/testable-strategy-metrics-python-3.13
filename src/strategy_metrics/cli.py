"""CLI: list Python tools and run derivations from the workbook catalog."""

from __future__ import annotations

import argparse
import json
import sys

from strategy_metrics.catalog import (
    load_metrics,
    load_primary_tool_bundle,
    load_primary_tools_manifest,
    primary_tools_index,
)
from strategy_metrics.tool_ids import primary_tool_slug
from strategy_metrics.derivations import apply_metric_pipeline


def cmd_list_tools() -> int:
    manifest = load_primary_tools_manifest()
    for entry in manifest.get("tools", []):
        print(
            f"{entry['primary_tool_id']}\t{entry['primary_tool']}\t{entry['metric_count']} metrics"
        )
    return 0


def cmd_show_tool(tool_ref: str) -> int:
    for loader in (
        lambda: load_primary_tool_bundle(primary_tool_id=tool_ref),
        lambda: load_primary_tool_bundle(primary_tool=tool_ref),
        lambda: load_primary_tool_bundle(primary_tool_id=primary_tool_slug(tool_ref)),
    ):
        try:
            bundle = loader()
            break
        except (ValueError, FileNotFoundError, OSError):
            bundle = None
    else:
        print(f"Unknown primary tool: {tool_ref}", file=sys.stderr)
        return 1
    print(json.dumps(bundle, indent=2, ensure_ascii=False))
    return 0


def cmd_show(metric_id: str) -> int:
    for row in load_metrics():
        if row.id == metric_id:
            print(json.dumps(row.__dict__, default=lambda o: o.__dict__, indent=2))
            return 0
    print(f"Unknown metric id: {metric_id}", file=sys.stderr)
    return 1


def cmd_apply(metric_id: str, variables_json: str) -> int:
    variables = json.loads(variables_json)
    for row in load_metrics():
        if row.id != metric_id:
            continue
        result = apply_metric_pipeline(
            derivation=row.derivation,
            normalization_formula=row.normalization_formula,
            variables=variables,
        )
        print(json.dumps(result, indent=2))
        return 0
    print(f"Unknown metric id: {metric_id}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Testable strategy metrics (Python 3.13)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-tools", help="List Python primary tools and metric counts")

    p_tool = sub.add_parser("show-tool", help="Show full data bundle for one primary tool")
    p_tool.add_argument(
        "tool",
        help="primary_tool_id (slug), or exact workbook name e.g. 'Coverage.py'",
    )

    p_show = sub.add_parser("show", help="Show one metric by id")
    p_show.add_argument("metric_id")

    p_apply = sub.add_parser("apply", help="Apply derivation + normalization")
    p_apply.add_argument("metric_id")
    p_apply.add_argument(
        "variables",
        help='JSON object of inputs, e.g. \'{"covered_branches": 8, "num_branches": 10}\'',
    )

    args = parser.parse_args(argv)
    if args.command == "list-tools":
        return cmd_list_tools()
    if args.command == "show-tool":
        return cmd_show_tool(args.tool)
    if args.command == "show":
        return cmd_show(args.metric_id)
    if args.command == "apply":
        return cmd_apply(args.metric_id, args.variables)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
