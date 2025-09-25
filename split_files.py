import os
from pathlib import Path


# --- Helper function for writing a HEPEVT chunk ---
def _write_hepevt_part(
    buffer_lines,
    output_dir,
    input_stem,
    file_index,
):
    """
    Writes a buffered set of lines as a new HEPEVT part file.
    Calculates particle count and prepends it as a header.
    Returns the incremented file_index.
    """
    # Count particle lines (excluding event headers if needed)
    # Assumes purely numeric lines are event headers, others are particle data
    particle_count = sum(1 for L in buffer_lines if not L.strip().isdigit())

    output_path = output_dir / f"{input_stem}_part_{file_index}.hepevt"
    with output_path.open("w") as outfile:
        outfile.write(f"{particle_count}\n")
        outfile.writelines(buffer_lines)

    return file_index + 1


# --------------------------------------------------


def split_hepevt_file(input_file, lines_per_file=5000, output_dir=None):
    input_path = Path(input_file)
    output_dir = Path(output_dir) if output_dir else input_path.parent / "split_hepevt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as input_file:
        next(
            input_file
        )  # Skip the first line of the input file (e.g., total event count)

        file_index = 0
        buffer_lines = []

        for line in input_file:
            buffer_lines.append(line)

            # Once we have enough lines, write them out
            if len(buffer_lines) >= lines_per_file:
                file_index = _write_hepevt_part(
                    buffer_lines, output_dir, input_path.stem, file_index
                )
                buffer_lines = []  # Clear the buffer for the next part

        # Write any remaining lines that didn't fill a whole part
        if buffer_lines:
            file_index = _write_hepevt_part(
                buffer_lines, output_dir, input_path.stem, file_index
            )

    print(f"Split '{input_path.name}' into {file_index} files in '{output_dir}'")


def split_all_hepevt_files_in_dir(lines_per_file=5000, file_pattern="*.hepevt"):
    dt_dir = os.environ["dtDir"]
    base_dir = Path(dt_dir + "/../backgrounds/SR_FCCee/SR_v5_cleaned_kevin")
    output_base_dir = Path(dt_dir + "/../split_up_SR_files")

    hepevt_files = list(base_dir.glob(file_pattern))
    if not hepevt_files:
        print(f"No HEPEVT files matching '{file_pattern}' found in '{base_dir}'")
        # Corrected 'directory' to 'base_dir' for clarity
        return

    for hepevt_file in hepevt_files:
        # Create a unique output directory for each original HEPEVT file
        sub_output_dir = output_base_dir / hepevt_file.stem
        split_hepevt_file(
            hepevt_file, lines_per_file=lines_per_file, output_dir=sub_output_dir
        )


# Run the main function to split all HEPEVT files
split_all_hepevt_files_in_dir()
