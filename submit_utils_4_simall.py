import subprocess


def submit_job(
    system_type,
    arguments,
    output_file_base_name,
    sub_jobs,
    bs_code_dir,
    executable_4KEK=None,
    more_rscrs=False,
):
    """Prepare and submit a job using the chosen batch system."""
    if system_type == "condor":
        # Create the Condor submit script
        exec_name = "condor_sub_exec.sh"
        condor_params = {
            "Universe": "vanilla",
            "Executable": exec_name,
            "Arguments": f'"{" ".join(arguments)}"',
            "transfer_input_files": bs_code_dir / exec_name,
            "Log": f"{output_file_base_name}.log",
            "Output": f"{output_file_base_name}.out",
            "Error": f"{output_file_base_name}.err",
            "environment": '"k4gDir=$ENV(k4gDir) codeDir=$ENV(codeDir)"',
        }
        if more_rscrs:
            condor_params["request_memory"] = 4096
            condor_params["request_runtime"] = 21600
        else:
            condor_params["request_memory"] = 2048

        # Create the script content using the dictionary
        condor_script_content = (
            "\n".join(f"{key} = {value}" for key, value in condor_params.items())
            + "\nQueue\n"
        )
        condor_submit_file = output_file_base_name.with_suffix(".condor")
        with open(condor_submit_file, "w", encoding="utf-8") as f:
            f.write(condor_script_content)

        condor_command = f"condor_submit {condor_submit_file}"
        if sub_jobs:
            subprocess.run(condor_command, shell=True, check=True)
        else:
            print(condor_command, end="\n\n")

    else:
        # Use bsub submission (used at KEK)
        output_log_file_name_4KEK = output_file_base_name.with_suffix(".log")
        arguments.extend(
            [
                ">",
                str(output_log_file_name_4KEK),
                "2>&1",
            ]
        )
        bsub_command = f'bsub -q l "{executable_4KEK} {" ".join(arguments)}"'
        if sub_jobs:
            subprocess.run(bsub_command, shell=True, check=True)
        else:
            print(bsub_command, end="\n\n")
