from pathlib import Path

from platform_paths import (
    SR_raw_input_dir,
    SR_split_input_dir,
    construct_SR_paths,
    flatten_bg_paths,
)
from scenario_folder_utils import (
    BX_PREFIX,
    N_ZERO_PADDING_BX,
    N_ZERO_PADDING_PART,
    PART_PREFIX,
    create_bx_subfolders,
)


# ================================================================
# Helper: write one HEPEVT chunk into a part file
# ================================================================
def _write_hepevt_part(
    buffer_lines, bx_output_dir, scenario_name, bx_index, part_index, flat_sr_paths_dict
):
    """
    Writes one buffered HEPEVT part file into the BX output directory.
    Prepends the particle count as header.
    """
    particle_count = sum(1 for L in buffer_lines if not L.strip().isdigit())
    output_name = (
        f"{flat_sr_paths_dict[scenario_name]}-{BX_PREFIX}{bx_index:0{N_ZERO_PADDING_BX}d}-"
        f"{PART_PREFIX}{part_index:0{N_ZERO_PADDING_PART}d}.hepevt"
    )
    output_path = bx_output_dir / output_name

    with output_path.open("w", encoding="utf-8") as outfile:
        outfile.write(f"{particle_count}\n")
        outfile.writelines(buffer_lines)

    return part_index + 1


# ================================================================
# Split one HEPEVT file into part files (one BX)
# ================================================================
def split_hepevt_file(
    input_file,
    bx_output_dir,
    scenario_name,
    bx_index,
    flat_sr_paths_dict,
    lines_per_file=20000,
):
    """
    Split a single HEPEVT input file (representing one BX) into part files.

    ```
    Parameters
    ----------
    input_file : Path or str
        Path to the .hepevt file representing one BX.
    bx_output_dir : Path
        Output directory for the split part files.
    scenario_name : str
        Base name for output file naming.
    bx_index : int
        Index of this BX.
    lines_per_file : int
        Number of lines per split part.
    """
    input_path = Path(input_file)
    bx_output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as infile:
        next(infile, None)  # Skip first line (total event count if present)

        part_index = 1
        buffer_lines = []

        for line in infile:
            buffer_lines.append(line)
            if len(buffer_lines) >= lines_per_file:
                part_index = _write_hepevt_part(
                    buffer_lines,
                    bx_output_dir,
                    scenario_name,
                    bx_index,
                    part_index,
                    flat_sr_paths_dict,
                )
                buffer_lines.clear()

        if buffer_lines:
            part_index = _write_hepevt_part(
                buffer_lines,
                bx_output_dir,
                scenario_name,
                bx_index,
                part_index,
                flat_sr_paths_dict,
            )

    print(
        f"BX {bx_index:0{N_ZERO_PADDING_BX}d}: Split '{input_path.name}' "
        f"into {part_index - 1} part files in '{bx_output_dir}'"
    )


# ================================================================
# Split all HEPEVT files (one scenario)
# ================================================================
def split_all_hepevt_files_in_scenario(
    raw_scenario_dir: Path,
    output_scenario_dir: Path,
    lines_per_file: int = None,
    file_pattern: str = "*.hepevt",
):
    """
    Split all HEPEVT files of one scenario.
    Each input file corresponds to one BX.
    """
    raw_scenario_dir = Path(raw_scenario_dir)
    output_scenario_dir = Path(output_scenario_dir)

    input_files = sorted(raw_scenario_dir.glob(file_pattern))
    if not input_files:
        print(
            f"No HEPEVT files matching '{file_pattern}' found in '{raw_scenario_dir}'"
        )
        return

    n_bx = len(input_files)
    bx_dirs = create_bx_subfolders(output_scenario_dir, n_bx)
    scenario_name = raw_scenario_dir.name

    print(f"Splitting scenario '{scenario_name}' with {n_bx} BX files...")

    flat_sr_paths = flatten_bg_paths(construct_SR_paths())

    for bx_index, (input_file, bx_output_dir) in enumerate(
        zip(input_files, bx_dirs), start=1
    ):
        if lines_per_file:
            split_hepevt_file(
                input_file,
                bx_output_dir,
                scenario_name,
                bx_index,
                flat_sr_paths,
                lines_per_file=lines_per_file,
            )
        else:
            split_hepevt_file(
                input_file,
                bx_output_dir,
                scenario_name,
                bx_index,
                flat_sr_paths,
            )


# ================================================================
# Main entry point for all scenarios
# ================================================================
def main():
    """
    Iterate over all scenario folders in SR_raw_input_dir.
    Each scenario is assumed to have multiple HEPEVT files (one per BX).
    """
    for raw_scenario_dir in sorted(SR_raw_input_dir.iterdir()):
        if not raw_scenario_dir.is_dir():
            continue

        output_scenario_dir = SR_split_input_dir / raw_scenario_dir.name
        split_all_hepevt_files_in_scenario(
            raw_scenario_dir, output_scenario_dir, lines_per_file=None
        )


if __name__ == "__main__":
    main()
