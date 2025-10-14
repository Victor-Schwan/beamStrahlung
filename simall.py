import argparse
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
    file_extensions,
)
from submit_utils_4_simall import submit_job

is_executed_on_DESY_NAF = identify_system() == DESY_NAF_MACHINE_IDENTIFIER

# define paths for later use
beamstrahlung_code_dir = code_dir / "beamStrahlung"
k4geoDir = get_path_from_env("k4gDir")
bs_data_paths, sr_data_paths = construct_paths(is_executed_on_DESY_NAF)

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

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Only process two input files for debugging",
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


def get_path(type_name: str, background: str) -> Path:
    if background == "beamstrahlung":
        data_paths = bs_data_paths
    else:
        data_paths = sr_data_paths
    return get_path_for_current_machine(data_paths[type_name])


def replace_BX_number_in_string(BX_n: int, path: Path) -> Path:
    return Path(str(path).replace("#N", str(BX_n).zfill(4)))


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
        # used to be input file path and might still be file path for bs
        input_folder_path = get_path(scenario_name, args.background)
        n_in_files = (
            sum(1 for p in input_folder_path.iterdir() if p.is_file())
            if args.background == "synchrotron"
            else args.bunchCrossingEnd + 1
        )

        # Debug mode: process only two input files
        if args.debug:
            if n_in_files > 2:
                n_in_files = 2

        print(f"{n_in_files} input files found for scenario: {scenario_name}")

        # loop over different input files corresponding to one background + scenario
        # loop over file paths nicer, when bs also always split
        for bunchcrossing in range(1, n_in_files + 1):
            if args.background == "beamstrahlung":
                # folder path used to be a file path here for bs
                folder_path_with_bX = replace_BX_number_in_string(
                    bunchcrossing, input_folder_path
                )
                input_file_path = folder_path_with_bX
            else:
                sr_file_suffix = (
                    f"_part_{bunchcrossing}.{file_extensions['synchrotron']}"
                )
                folder_path_with_bX = input_folder_path
                input_file_path = [
                    p
                    for p in input_folder_path.iterdir()
                    if p.is_file() and p.name.endswith(sr_file_suffix)
                ]
                if len(input_file_path) != 1:
                    raise FileNotFoundError(
                        f"Expected exactly one file ending with '{sr_file_suffix}'"
                    )
                input_file_path = input_file_path[0]  # to avoid to confuse the linter

            if not input_file_path.exists():
                print(
                    f"\nThere are only {bunchcrossing - 1} files for {scenario_name} available",
                    end="\n\n",
                )
                break

            if args.debug:
                print(f"Input file path: {input_file_path}\n")

            # Iterate over the detector models
            for det_mod_name, det_mod_configs in det_mod_configs_dict_filtered.items():
                out_dir = (
                    parent_out_dir / det_mod_name / f"{scenario_name}_{bunchcrossing}"
                )

                out_dir.mkdir(parents=True, exist_ok=True)

                # Construct the output file names
                out_name = (
                    out_dir
                    / f"{det_mod_name}-{scenario_name}-{'part' if args.background == 'synchrotron' else f'nEvts_{args.nEvents}-bX'}_{str(bunchcrossing).zfill(4)}"
                )
                if args.debug:
                    print(
                        f"Output file name: {out_name.with_suffix(edm4hep_file_suffix)}"
                    )

                # Define the executable and arguments separately
                executable = "ddsim"
                arguments = [
                    "--steeringFile",
                    str(beamstrahlung_code_dir / "ddsim_keep_microcurlers_10MeV.py"),
                    "--compactFile",
                    str(k4geoDir / det_mod_configs.get_compact_file_path()),
                    "--inputFile",
                    str(input_file_path),
                    "--outputFile",
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

                if args.background == "beamstrahlung":
                    # Add particles per event argument
                    arguments.extend(
                        [
                            "--numberOfEvents",
                            str(args.nEvents),
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
