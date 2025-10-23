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

import re
from pathlib import Path

from tabulate import tabulate
from platform_paths import edm4hep_file_suffix

# === Configuration constants ===
N_ZERO_PADDING_BX = 4
N_ZERO_PADDING_PART = 4
DEFAULT_MAX_DEBUG_BX = 2
DEFAULT_MAX_DEBUG_PARTS = 2
BX_PREFIX = "BX_"
PART_PREFIX = "part_"


# === Discovery functions ===
def discover_bx_folders(scenario_folder: Path) -> list[Path]:
    """
    Return a sorted list of BX subfolders in the given scenario folder.
    If none are found, return [scenario_folder] assuming a single-BX layout.
    """
    bx_pattern = re.compile(rf"^{BX_PREFIX}\d{{{N_ZERO_PADDING_BX}}}$")
    bx_folders = sorted(
        [
            p
            for p in scenario_folder.iterdir()
            if p.is_dir() and bx_pattern.match(p.name)
        ]
    )
    if not bx_folders:
        # fallback: no subfolders, assume single BX
        return [scenario_folder]
    return bx_folders


def discover_parts_in_bx(bx_folder: Path, suffix: str) -> list[Path]:
    """
    Return a sorted list of part files in the BX folder.
    Matches filenames ending with '_BX_####_part_####<suffix>'.
    """
    # Build regex to extract the part index
    part_pattern = re.compile(
        rf"_{BX_PREFIX}\d{{{N_ZERO_PADDING_BX}}}_{PART_PREFIX}(\d{{{N_ZERO_PADDING_PART}}}){re.escape(suffix)}$"
    )

    parts = []
    for f in bx_folder.iterdir():
        if f.is_file() and part_pattern.search(f.name):
            parts.append(f)

    # Sort numerically by the part index extracted from filename
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
    """
    Discover all BX folders and their corresponding part files.
    Returns a mapping {bx_index: [Path, ...]}.

    If debug=True, limits to at most `max_debug_bx` BXs and `max_debug_parts` parts per BX.
    """
    bx_folders = discover_bx_folders(scenario_folder)

    bx_to_parts: dict[int, list[Path]] = {}
    bad_bx_folders = []
    for bx_index, bx_folder in enumerate(bx_folders, start=1):
        parts = discover_parts_in_bx(bx_folder, suffix)
        if not parts:
            bad_bx_folders.append(bx_folder.name)
            continue

        if debug:
            parts = parts[:max_debug_parts]

        bx_to_parts[bx_index] = parts

    if bad_bx_folders:
        print(f"Warning: no part files found in {bad_bx_folders}")

    if debug and len(bx_to_parts) > max_debug_bx:
        bx_to_parts = {k: v for k, v in list(bx_to_parts.items())[:max_debug_bx]}

    return bx_to_parts


# === Creation and validation ===
def create_bx_subfolders(base_folder: Path, n_bx: int) -> list[Path]:
    """
    Create BX subfolders BX_0001 ... BX_NNNN in base_folder.
    Returns the created Path list.
    """
    created = []
    for i in range(1, n_bx + 1):
        bx_folder = base_folder / f"{BX_PREFIX}{i:0{N_ZERO_PADDING_BX}d}"
        bx_folder.mkdir(parents=True, exist_ok=True)
        created.append(bx_folder)
    return created


def validate_scenario_structure(scenario_folder: Path, suffix: str) -> bool:
    """
    Check that the scenario folder follows the BX/part structure rules.
    Print a tabulated summary of BX folders and part counts.
    Returns True if structure looks valid, False otherwise.
    """
    if not scenario_folder.exists():
        print(f"Error: folder does not exist: {scenario_folder}")
        return False

    bx_folders = discover_bx_folders(scenario_folder)
    if not bx_folders:
        print(f"No BX folders found in {scenario_folder}")
        return False

    rows = []
    valid = True
    for bx_folder in bx_folders:
        parts = discover_parts_in_bx(bx_folder, suffix)
        n_parts = len(parts)
        example = parts[0].name if parts else "(none)"
        rows.append([bx_folder.name, n_parts, example])
        if n_parts == 0:
            valid = False

    # if more than 24 entries, print only first, middle and last 7 rows
    l_rows = len(rows)
    if l_rows > 24:
        blind_row = [
            [
                "...",
            ]
            * 3
        ]
        rows = (
            rows[0:7]
            + blind_row
            + rows[l_rows // 2 - 3 : l_rows // 2 + 4]
            + blind_row
            + rows[-7:]
        )

    table = tabulate(
        rows, headers=["BX folder", "#parts", "Example file"], tablefmt="grid"
    )
    print(f"\nScenario folder: {scenario_folder}")
    print(table)

    return valid


########################################################################
# interactive part, if this script is directly called
########################################################################


def check_substructure(user_input):
    user_path = Path(user_input)

    if not user_path.is_dir():
        print(f"The path {user_path} does not exist or is not a directory.")
        return False

    if validate_scenario_structure(user_path, edm4hep_file_suffix):
        print("The given path seems to fulfil the structure.")
    else:
        print("The given path does not stick to the standard structure!")


def interactive_shell():
    from IPython import embed

    embed()


def main():
    while True:
        # Ask user for a path
        user_input = input(
            "Enter a path to check (or 'exit' to quit, 'shell' for interactive shell): "
        )

        if user_input.lower() == "exit":
            print("Exiting script.")
            break
        elif user_input.lower() == "shell":
            interactive_shell()
            continue

        # Check if the path exists and if it meets the required structure
        if check_substructure(user_input):
            action = input("Do you want to check another path? (yes/no): ").lower()
            if action != "yes":
                print("Ending script.")
                break
        else:
            print("Please try again with a valid path.")


if __name__ == "__main__":
    main()
