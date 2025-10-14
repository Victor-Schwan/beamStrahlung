import argparse
import os
from glob import glob
from pathlib import Path

from det_mod_configs import (
    CHOICES_DETECTOR_MODELS,
    DEFAULT_DETECTOR_MODELS,
    get_paths_and_detector_configs,
)
from platform_paths import (
    DESY_NAF_MACHINE_IDENTIFIER,
    SIM_DATA_SUBDIR_NAME,
    code_dir,
    construct_paths,
    get_path_for_current_machine,
    identify_system,
    get_path_from_env,
    edm4hep_file_suffix,
)
from submit_utils_4_simall import submit_job

is_executed_on_DESY_NAF = identify_system() == DESY_NAF_MACHINE_IDENTIFIER

# define paths for later use
beamstrahlung_code_dir = code_dir / "beamStrahlung"
k4geoDir = get_path_from_env("k4gDir")
bs_data_paths, sr_data_paths, file_extensions = construct_paths(is_executed_on_DESY_NAF)

# single source of truth, keys of bs_data_paths become values of tuple
CHOICES_SCENARIOS = {
    "synchrotron": tuple(sr_data_paths),
    "beamstrahlung": tuple(bs_data_paths),
}
DEFAULT_SCENARIOS = {
    "synchrotron": ("182GeV_nzco_10urad",),
    "beamstrahlung": ("FCC240",),
}


# Dict containing the detector model configurations
det_mod_configs_dict = get_paths_and_detector_configs()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process simulation parameters for FCCee and ILC."
    )

    parser.add_argument(
        "--bunchCrossingEnd",
        type=int,
        default=2,
        help="End value for bunch crossing (default: 2)",
    )

    parser.add_argument(
        "--nEvents",
        type=int,
        default=5000,
        help="Number of events to simulate (default: 5000)",
    )

    parser.add_argument(
        "--guineaPigPartPerE",
        type=int,
        default=-1,
    )

    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="Version name for the simulation",
    )

    parser.add_argument(
        "--background",
        type=str,
        choices=CHOICES_SCENARIOS.keys(),
        help="Type of background data to read",
    )

    parser.add_argument(
        "--detectorModel",
        choices=CHOICES_DETECTOR_MODELS,
        nargs="+",
        default=DEFAULT_DETECTOR_MODELS,
        help="Detector models to analyze (choose one or more)",
    )

    parser.add_argument(
        "--scenario",
        nargs="+",
        help="Accelerator configurations to analyze (choose one or more)",
    )

    parser.add_argument(
        "--submit_jobs", action="store_true", help="Submit job(s) if this flag is set"
    )

    return parser.parse_args()


def get_args(parse_args=parse_arguments):
    args = parse_args()

    if args.background is None:
        if args.version in CHOICES_SCENARIOS:
            args.background = args.version
        else:
            args.background = "beamstrahlung"

    # Apply default if not specified
    if args.scenario is None:
        args.scenario = list(DEFAULT_SCENARIOS[args.background])

    # Validate manually
    valid_choices = CHOICES_SCENARIOS[args.background]
    for sc in args.scenario:
        if sc not in valid_choices:
            print(
                f" Error: when background={args.background}, scenario must be one of {valid_choices}. Got '{sc}'"
            )
            args.scenario = list(DEFAULT_SCENARIOS[args.background])

    return args


def replace_BX_number_in_string(type_name: str, BX_n: int, background: str) -> str:
    if background == "beamstrahlung":
        data_paths = bs_data_paths
    else:
        data_paths = sr_data_paths

    if type_name == "ILC250":
        return str(get_path_for_current_machine(data_paths[type_name])).replace(
            "#N", str(BX_n).zfill(4)
        )
    return str(get_path_for_current_machine(data_paths[type_name])).replace(
        "#N", str(BX_n)
    )


def check_max_BX_number_exceeded(bs_type_name: str, bunchcrossing: int) -> bool:
    """
    Check whether maximum number of bunch crossings per beam strahlung type is exceeded.
    """
    if bs_type_name in {"FCC240", "FCC091"} and bunchcrossing > 450:
        print(
            f"\nThere are only 450 bunch crossing for {bs_type_name} available",
            end="\n\n",
        )
        return True
    if bs_type_name == "ILC250" and bunchcrossing > 1312:
        print(
            f"\nThere are only 1312 bunch crossing for {bs_type_name} available",
            end="\n\n",
        )
        return True
    return False


def save_bX_count(scenario, background, out_dir):
    first_bx_path = Path(replace_BX_number_in_string(scenario, 1, background))
    if first_bx_path.exists():
        input_folder = first_bx_path.parent
        if background == "synchrotron":
            num_bx = 1
        else:
            num_bx = sum(1 for f in input_folder.iterdir() if f.is_file())
        bx_count_file = out_dir / f"{scenario}_number_of_bx.txt"
        with open(bx_count_file, "w") as f:
            f.write(f"{num_bx}\n")
    else:
        print(f"⚠️ No files found for scenario {scenario}, skipping count.")


def main():
    # # Function to simulate sourcing (can only be done inside the same shell process)
    # def source_setup_script(script):
    #     return subprocess.run(
    #         f"source {script} && env", shell=True, capture_output=True, text=True
    #     )

    # # Note: The setup script source cannot affect the Python environment, but we simulate it in case needed.
    # source_setup_script(setupScriptPath)  # This will not affect the Python environment

    args = get_args()
    parent_out_dir = (
        Path(get_path_from_env("dtDir")) / SIM_DATA_SUBDIR_NAME / args.version
    )
    parent_out_dir.mkdir(parents=True, exist_ok=True)

    det_mod_configs_dict_filtered = {
        key: value
        for key, value in det_mod_configs_dict.items()
        if key in args.detectorModel
    }

    # Iterate over the beam strahlung scenarios
    for scenario_name in args.scenario:
        # loop over different files, bX is file index
        for bunchcrossing in range(1, args.bunchCrossingEnd + 1):
            folder_path_with_bX = replace_BX_number_in_string(
                scenario_name, bunchcrossing, args.background
            )
            print(folder_path_with_bX)
            if not os.path.exists(folder_path_with_bX):
                print(
                    f"\nThere are only {bunchcrossing - 1} files for {scenario_name} available",
                    end="\n\n",
                )
                break

            # Iterate over the detector models
            for det_mod_name, det_mod_configs in det_mod_configs_dict_filtered.items():
                out_dir = (
                    parent_out_dir / det_mod_name / f"{scenario_name}_{bunchcrossing}"
                )

                out_dir.mkdir(parents=True, exist_ok=True)

                input_files = glob(
                    os.path.join(
                        folder_path_with_bX, f"*.{file_extensions[args.background]}"
                    )
                )

                for i, input_file_path in enumerate(input_files):
                    # Construct the output file names
                    out_name = (
                        out_dir
                        / f"{det_mod_name}-{scenario_name}-bX_{str(bunchcrossing).zfill(4)}-nEvts_{args.nEvents}-part_{i}"
                    )

                    print(folder_path_with_bX)

                    # Define the executable and arguments separately
                    executable = "ddsim"
                    arguments = [
                        "--steeringFile",
                        str(
                            beamstrahlung_code_dir / "ddsim_keep_microcurlers_10MeV.py"
                        ),
                        "--compactFile",
                        str(k4geoDir / det_mod_configs.get_compact_file_path()),
                        "--inputFile",
                        str(input_file_path),
                        "--outputFile",
                        "--numberOfEvents",
                        str(args.nEvents),
                        str(out_name.with_suffix(edm4hep_file_suffix)),
                        "--crossingAngleBoost",
                        str(det_mod_configs.get_crossing_angle()),
                    ]

                    if det_mod_configs.is_accelerator_ilc:
                        # increased resources needed
                        more_resources = True
                        # Determine particles per event value for "ILC" scenario
                        particles_per_event = (
                            str(args.guineaPigPartPerE)
                            if 1 <= args.guineaPigPartPerE <= 5000
                            else str(5000)
                        )
                    else:
                        # Use the provided particles per event for non-"ILC" scenarios
                        particles_per_event = str(args.guineaPigPartPerE)

                    # Add particles per event argument
                    arguments.extend(
                        [
                            "--guineapig.particlesPerEvent",
                            particles_per_event,
                        ]
                    )

                    # Decide whether to use Condor or bsub
                    batch_system = "condor" if is_executed_on_DESY_NAF else "bsub"

                    # Submit the job using the appropriate batch system
                    submit_job(
                        batch_system,
                        arguments,
                        out_name,
                        args.submit_jobs,
                        beamstrahlung_code_dir,
                        executable,
                        more_rscrs=more_resources,
                    )


if __name__ == "__main__":
    main()
