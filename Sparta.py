#!/usr/bin/env python3
"""Command-line entry point for calculating a Sparta round."""

from __future__ import annotations

import argparse
from pathlib import Path

from sparta import InputError, load_round, settle_round
from sparta.report import write_csv, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle a Sparta golf scorecard")
    parser.add_argument("input", nargs="?", type=Path, help="input scorecard CSV")
    parser.add_argument("--inputFile", dest="legacy_input", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("-o", "--output", type=Path, help="output path (default: <input>_Output.csv)")
    parser.add_argument("--format", choices=("csv", "json"), help="output format inferred from extension by default")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input or args.legacy_input
    if source is None:
        raise SystemExit("an input scorecard CSV is required")
    output_format = args.format or ("json" if args.output and args.output.suffix == ".json" else "csv")
    output = args.output or source.with_name(f"{source.stem}_Output.{output_format}")

    try:
        _, players = load_round(source)
        result = settle_round(players)
    except (InputError, ValueError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    if output_format == "json":
        write_json(result, output)
    else:
        write_csv(result, output)
    print(f"Settled {len(players)} players; wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
