import argparse
import re
from pathlib import Path

from platform_paths import file_extensions

from scenario_folder_utils import (
    BX_PREFIX,
    N_ZERO_PADDING_BX,
    N_ZERO_PADDING_PART,
    PART_PREFIX,
)


def apply_vertex_correction(input_file: Path) -> list[str]:
    """
    Reads a GuineaPig file and resets vertices (indices 4, 5, 6) to 0.
    """
    processed_lines = []
    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 7:
                continue
            # Reset vertex to (0,0,0)
            parts[4], parts[5], parts[6] = "0", "0", "0"
            processed_lines.append(" ".join(parts) + " \n")
    return processed_lines


def get_input_mapping(input_dir: Path) -> dict[int, Path]:
    """
    Detects the input structure and returns a mapping of {bx_index: file_path}.
    Supports:
      1. subfolder structure (input_dir/data#/pairs.pairs)
      2. flat structure (input_dir/output_#.pairs or any filename containing digits)
    """
    mapping = {}

    # Try 1: Subfolder structure (data123/pairs.pairs)
    data_folder_pattern = re.compile(r"data(\d+)")
    subdirs = [
        d
        for d in input_dir.iterdir()
        if d.is_dir() and data_folder_pattern.match(d.name)
    ]

    if subdirs:
        for subdir in subdirs:
            idx = int(data_folder_pattern.match(subdir.name).group(1))
            f_path = subdir / "pairs.pairs"
            if f_path.exists():
                mapping[idx] = f_path
        return mapping

    # Try 2: Flat structure (e.g. output_123.pairs)
    flat_file_pattern = re.compile(r".*?(\d+)\.pairs$")
    for f_path in input_dir.glob("*.pairs"):
        match = flat_file_pattern.match(f_path.name)
        if match:
            idx = int(match.group(1))
            mapping[idx] = f_path

    return mapping


def main():
    parser = argparse.ArgumentParser(
        description="Standardize IPC data naming and structure for k4hep/simall."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Input directory (data# folders or flat .pairs files)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory where BX_#### structure will be created",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        type=str,
        default=None,
        help="Scenario name for filename. Defaults to output directory name.",
    )
    parser.add_argument(
        "--correct_vertex",
        action="store_true",
        help="Apply (0,0,0) vertex correction to GuineaPig files",
    )

    args = parser.parse_args()

    # Setup suffix and scenario name
    suffix = file_extensions.get("beamstrahlung", ".pairs")
    scenario_name = args.scenario if args.scenario else args.output.name

    input_map = get_input_mapping(args.input)

    if not input_map:
        print(f"No valid input files found in {args.input}")
        return

    print(f"Scenario: {scenario_name}")
    print(
        f"Found {len(input_map)} BX files. Processing (Correction: {args.correct_vertex})..."
    )

    # Ensure output base exists
    args.output.mkdir(parents=True, exist_ok=True)

    for bx_index, input_path in sorted(input_map.items()):
        # Create output directory structure (BX_####)
        bx_folder_name = f"{BX_PREFIX}{bx_index:0{N_ZERO_PADDING_BX}d}"
        target_dir = args.output / bx_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Harmonized Filename: scenario-BX_####-part_####.pairs
        out_file_name = (
            f"{scenario_name}-{bx_folder_name}-"
            f"{PART_PREFIX}{1:0{N_ZERO_PADDING_PART}d}{suffix}"
        )
        output_path = target_dir / out_file_name

        if args.correct_vertex:
            lines = apply_vertex_correction(input_path)
            with output_path.open("w", encoding="utf-8") as f:
                f.writelines(lines)
        else:
            # Efficiently copy if no correction is needed
            output_path.write_text(
                input_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

    print(f"Done. Files prepared in: {args.output}")


if __name__ == "__main__":
    main()
