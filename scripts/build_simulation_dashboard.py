"""Build a parser-compatible simulation dashboard YAML from row component files.

Home Assistant Lovelace in this setup does not support !include in dashboard files.
This script lets you keep modular row files and emits one monolithic
`config/dashboards/simulation_dashboard.yaml` for deployment.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROWS_DIR = ROOT / "config" / "dashboards" / "simulation"
OUTPUT_FILE = ROOT / "config" / "dashboards" / "simulation_dashboard.yaml"

ROW_FILES = [
    "row1_controls.yaml",
    "row2_meetwaarden.yaml",
    "row3_period_card.yaml",
    "row4_referentietabel.yaml",
]

HEADER = [
    "views:",
    "  - title: Simulatie Mevrouw Goedheid",
    "    path: simulatie-goedheid",
    "    icon: mdi:scale-bathroom",
    "    type: masonry",
    "    cards:",
]


def _load_row_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing row file: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        raise ValueError(f"Row file is empty: {path}")

    return lines


def build_dashboard() -> str:
    output: list[str] = list(HEADER)

    for filename in ROW_FILES:
        row_path = ROWS_DIR / filename
        row_lines = _load_row_lines(row_path)

        output.append(f"      - {row_lines[0]}")
        output.extend(f"        {line}" for line in row_lines[1:])

    return "\n".join(output) + "\n"


def main() -> None:
    content = build_dashboard()
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Built: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
