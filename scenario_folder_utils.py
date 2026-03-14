"""
scenario_folder_utils.py

Utilities for handling the standardized folder structure of simulated detector data.

Folder structure conventions
----------------------------
Each "scenario folder" may contain subfolders for each bunch crossing (BX).
BX folders are named according to the pattern:

    BX_####

where #### is a zero-padded integer with N_ZERO_PADDING_BX digits.

Inside each BX folder (or directly inside the scenario folder if only one BX),
the files representing split parts of that BX follow the pattern:

    [prefix]_BX_####_part_####[suffix]

where the first #### refers to the BX index and the second to the part index,
padded with N_ZERO_PADDING_BX and N_ZERO_PADDING_PART digits respectively.

This module provides:
- discovery of BX folders and part files
- validation and summary printing
- creation of BX subfolders for new scenarios
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from tabulate import tabulate

# Single Source of Truth Imports
from platform_paths import edm4hep_file_suffix, lcio_file_suffix, file_extensions

# === Configuration constants ===
N_ZERO_PADDING_BX = 6
N_ZERO_PADDING_PART = 6
DEFAULT_MAX_DEBUG_BX = 2
DEFAULT_MAX_DEBUG_PARTS = 2
BX_PREFIX = "BX_"
PART_PREFIX = "part_"

# Map for CLI choices
VALID_EXTENSIONS = {
    "pairs": file_extensions.get("beamstrahlung", ".pairs"),
    "hepevt": file_extensions.get("synchrotron", ".hepevt"),
    "edm4hep": edm4hep_file_suffix,
    "lcio": lcio_file_suffix,
}


# === Discovery functions ===
def discover_bx_folders(scenario_folder: Path) -> list[Path]:
    """
    Return a sorted list of BX subfolders (BX_####) in the scenario folder.
    Fallback: returns [scenario_folder] if no BX subfolders are found.
    """
    bx_pattern = re.compile(rf"^{BX_PREFIX}\d{{{N_ZERO_PADDING_BX}}}$")
    bx_folders = sorted(
        [
            p
            for p in scenario_folder.iterdir()
            if p.is_dir() and bx_pattern.match(p.name)
        ]
    )
    return bx_folders if bx_folders else [scenario_folder]


def discover_parts_in_bx(bx_folder: Path, suffix: str) -> list[Path]:
    """
    Return a sorted list of part files in the BX folder.
    Matches harmonized format: -BX_####-part_####<suffix>
    """
    part_pattern = re.compile(
        rf"-{BX_PREFIX}\d{{{N_ZERO_PADDING_BX}}}-{PART_PREFIX}(\d{{{N_ZERO_PADDING_PART}}}){re.escape(suffix)}$"
    )

    parts = [
        f for f in bx_folder.iterdir() if f.is_file() and part_pattern.search(f.name)
    ]

    def extract_index(path: Path) -> int:
        match = part_pattern.search(path.name)
        return int(match.group(1)) if match else 0

    parts.sort(key=extract_index)
    return parts


def collect_all_parts(
    scenario_folder: Path,
    suffix: str,
    debug: bool = False,
    max_debug_bx: int = DEFAULT_MAX_DEBUG_BX,
    max_debug_parts: int = DEFAULT_MAX_DEBUG_PARTS,
) -> dict[int, list[Path]]:
    """Mapping of {bx_index: [list of part Paths]}."""
    bx_folders = discover_bx_folders(scenario_folder)
    bx_to_parts: dict[int, list[Path]] = {}

    for bx_index, bx_folder in enumerate(bx_folders, start=1):
        parts = discover_parts_in_bx(bx_folder, suffix)
        if not parts:
            continue
        if debug:
            parts = parts[:max_debug_parts]
        bx_to_parts[bx_index] = parts

    if debug and len(bx_to_parts) > max_debug_bx:
        bx_to_parts = dict(list(bx_to_parts.items())[:max_debug_bx])

    return bx_to_parts


def validate_scenario_structure(scenario_folder: Path, suffix: str) -> bool:
    """Prints a tabulated summary of the scenario structure."""
    if not scenario_folder.exists():
        print(f"Error: Path does not exist: {scenario_folder}")
        return False

    bx_folders = discover_bx_folders(scenario_folder)
    rows = []
    valid = True

    for bx_folder in bx_folders:
        parts = discover_parts_in_bx(bx_folder, suffix)
        n_parts = len(parts)
        example = parts[0].name if parts else "(NONE FOUND)"
        rows.append([bx_folder.name, n_parts, example])
        if n_parts == 0:
            valid = False

    # Truncate long tables for readability
    display_rows = rows
    if len(rows) > 24:
        display_rows = (
            rows[:7]
            + [["...", "...", "..."]]
            + rows[len(rows) // 2 - 3 : len(rows) // 2 + 4]
            + [["...", "...", "..."]]
            + rows[-7:]
        )

    print(f"\nScenario: {scenario_folder}")
    print(
        tabulate(
            display_rows,
            headers=["BX Folder", "# Parts", "Example File"],
            tablefmt="grid",
        )
    )

    return valid


def main():
    parser = argparse.ArgumentParser(
        description="Validate standardized HEP data structures."
    )
    parser.add_argument(
        "path", type=Path, help="Path to the scenario folder to validate"
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=VALID_EXTENSIONS.keys(),
        default="edm4hep",
        help="Type of files to look for (suffix mapping)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Test discovery logic with debug limits"
    )

    args = parser.parse_args()
    suffix = VALID_EXTENSIONS[args.type]

    print(f"Validating for file type: {args.type} (suffix: {suffix})")

    is_valid = validate_scenario_structure(args.path, suffix)

    if is_valid:
        print("\nSUCCESS: Structure matches the standard convention.")
    else:
        print("\nFAILURE: Missing files or incorrect naming in one or more BX folders.")


if __name__ == "__main__":
    main()
