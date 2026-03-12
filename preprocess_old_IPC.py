import argparse
import re
from pathlib import Path
from scenario_folder_utils import (
    N_ZERO_PADDING_BX,
    N_ZERO_PADDING_PART,
    BX_PREFIX,
    PART_PREFIX,
)

DEFAULT_SUFFIX = ".pairs"


def process_ipc_files(input_dir: Path, output_dir: Path):
    """
    Parses GuineaPig IPC files, resets vertices to (0,0,0), and organizes
    them into the folder structure expected by scenario_folder_utils.
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path {input_dir} is not a directory.")

    # Match folders named 'data1', 'data2', etc.
    data_folder_pattern = re.compile(r"data(\d+)")

    # Find all matching directories
    subdirs = [
        d
        for d in input_dir.iterdir()
        if d.is_dir() and data_folder_pattern.match(d.name)
    ]

    if not subdirs:
        print(f"No 'data#' directories found in {input_dir}")
        return

    print(f"Found {len(subdirs)} data directories. Processing...")

    for subdir in sorted(subdirs):
        # Extract BX index from folder name (e.g., 'data123' -> 123)
        bx_match = data_folder_pattern.match(subdir.name)
        bx_index = int(bx_match.group(1))

        # Expected input file
        input_file = subdir / "pairs.pairs"
        if not input_file.exists():
            print(f"  Skipping {subdir.name}: 'pairs.pairs' not found.")
            continue

        # Create output structure: output_dir/BX_0123/
        bx_folder_name = f"{BX_PREFIX}{bx_index:0{N_ZERO_PADDING_BX}d}"
        target_dir = output_dir / bx_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Output filename: prefix_BX_0123_part_0001.pairs
        # We assume part 1 as there is only one file per BX
        out_file_name = (
            f"guineaPig_{bx_folder_name}_{PART_PREFIX}"
            f"{1:0{N_ZERO_PADDING_PART}d}{DEFAULT_SUFFIX}"
        )
        output_file = target_dir / out_file_name

        print(f"  Processing {subdir.name} -> {bx_folder_name}/{out_file_name}")

        processed_lines = []
        with input_file.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 7:
                    continue

                # GuineaPig format indices for position: 4, 5, 6 (x, y, z)
                # We set them to "0" as per the requirement
                parts[4] = "0"
                parts[5] = "0"
                parts[6] = "0"

                processed_lines.append(" ".join(parts) + " \n")

        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(processed_lines)

    print("\nProcessing complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare GuineaPig IPC data for k4hep/simall processing."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the raw data folder containing data# subdirectories.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path where the prepared BX_#### structure will be created.",
    )

    args = parser.parse_args()

    try:
        process_ipc_files(args.input, args.output)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
