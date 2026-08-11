"""Generator obrazków stanów gry (Baśka) — do przykładów w tłumaczeniach."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .table import save_state, state_from_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generuje PNG ze stanem gry (4 gracze, ręce 0–4, stos ≤3)."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Pliki JSON ze stanem gry. Bez argumentów: wszystkie w examples/",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        default="output",
        help="Katalog wyjściowy (domyślnie: output/)",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir

    if args.inputs:
        files = [Path(p) for p in args.inputs]
    else:
        examples = root / "examples"
        files = sorted(examples.glob("*.json")) if examples.is_dir() else []
        if not files:
            print("Brak plików JSON. Podaj ścieżkę lub wrzuć pliki do examples/.", file=sys.stderr)
            return 1

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        state = state_from_dict(data)
        out_name = data.get("output") or f"{path.stem}.png"
        out_path = out_dir / out_name
        save_state(state, out_path)
        print(f"OK  {path.name} -> {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
