from pathlib import Path
import os

def split_hepevt_f1ile(input_file, lines_per_file=5000, output_dir=None):
    input_path = Path(input_file)
    output_dir = Path(output_dir) if output_dir else input_path.parent / "split_hepevt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r") as infile:
        file_index = 0
        lines_written = 0
        outfile = None

        for line in infile:
            if lines_written == 0:
                if outfile:
                    outfile.close()
                output_path = output_dir / f"{input_path.stem}_part_{file_index}.hepevt"
                outfile = output_path.open("w")
                file_index += 1

            outfile.write(line)
            lines_written += 1

            if lines_written >= lines_per_file:
                lines_written = 0

        if outfile:
            outfile.close()

    print(f"Split '{input_path.name}' into {file_index} files in '{output_dir}'")


def split_hepevt_file(input_file, lines_per_file=5000, output_dir=None):
    input_path = Path(input_file)
    output_dir = Path(output_dir) if output_dir else input_path.parent / "split_hepevt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r") as infile:
        next(infile)  # Skip the first line of the input file

        file_index = 0
        lines_written = 0
        outfile = None
        buffer_lines = []

        for line in infile:
            buffer_lines.append(line)

            # Once we have enough lines, write them out
            if len(buffer_lines) >= lines_per_file:
                # Count particle lines (excluding event headers if needed)
                particle_count = sum(
                    1 for l in buffer_lines if not l.strip().isdigit()
                )

                output_path = output_dir / f"{input_path.stem}_part_{file_index}.hepevt"
                with output_path.open("w") as outfile:
                    outfile.write(f"{particle_count}\n")
                    outfile.writelines(buffer_lines)

                file_index += 1
                buffer_lines = []

        # Write remaining lines
        if buffer_lines:
            particle_count = sum(
                1 for l in buffer_lines if not l.strip().isdigit()
            )
            output_path = output_dir / f"{input_path.stem}_part_{file_index}.hepevt"
            with output_path.open("w") as outfile:
                outfile.write(f"{particle_count}\n")
                outfile.writelines(buffer_lines)
            file_index += 1

    print(f"Split '{input_path.name}' into {file_index} files in '{output_dir}'")

def split_all_hepevt_files_in_dir(lines_per_file=5000, file_pattern="*.hepevt"):
    dt_dir = os.environ["dtDir"] 
    base_dir = Path(dt_dir + '/../backgrounds/SR_FCCee/SR_v5_cleaned_kevin')
    output_base_dir = Path(dt_dir + '/../split_up_SR_files')

    hepevt_files = list(base_dir.glob(file_pattern))
    if not hepevt_files:
        print(f"No HEPEVT files matching '{file_pattern}' found in '{directory}'")
        return

    for hepevt_file in hepevt_files:
        sub_output_dir = output_base_dir / hepevt_file.stem
        split_hepevt_file(hepevt_file, lines_per_file=lines_per_file, output_dir=sub_output_dir)

split_all_hepevt_files_in_dir()
