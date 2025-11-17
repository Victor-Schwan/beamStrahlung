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
    edm4hep_file_suffix,
    file_extensions,
    get_path_for_current_machine,
    get_path_from_env,
    identify_system,
)
from scenario_folder_utils import BX_PREFIX, N_ZERO_PADDING_BX, collect_all_parts
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
        default=1,
        help="Number of events to simulate (default: 1)",
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
        help="Accelerator configurations to analyze (choose one or more), or 'all' to use all available ones",
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

    # '--scenario all' as shortcut to process all
    if len(args.scenario) == 1 and args.scenario[0].lower() == "all":
        args.scenario = list(CHOICES_SCENARIOS[args.background])

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

    for scenario_name in args.scenario:
        input_folder_path = get_path(scenario_name, args.background)
        bx_to_parts = collect_all_parts(
            input_folder_path,
            file_extensions[args.background],
            debug=args.debug,
        )

        print(f"\nProcessing scenario '{scenario_name}' with {len(bx_to_parts)} BXs")

        # Iterate over each bunch crossing (BX) and its corresponding split part files
        for bx_index, part_files in bx_to_parts.items():
            print(f"  BX {bx_index:0{N_ZERO_PADDING_BX}d}: {len(part_files)} parts")

            # Process each split part file within this BX
            for part_file in part_files:
                if not part_file.exists():
                    print(f"    Missing part file: {part_file}")
                    continue

                # Loop over all selected detector models
                for (
                    det_mod_name,
                    det_mod_configs,
                ) in det_mod_configs_dict_filtered.items():
                    # Create output directory for this detector & BX
                    out_dir = (
                        parent_out_dir
                        / det_mod_name
                        / f"{scenario_name}"
                        / f"{BX_PREFIX}{bx_index:0{N_ZERO_PADDING_BX}d}"
                    )
                    out_dir.mkdir(parents=True, exist_ok=True)

                    # Output file base name (preserves part info)
                    part_stem = part_file.stem  # e.g. scenario_BX_0001_part_0001
                    out_name = out_dir / f"{det_mod_name}-{part_stem}"

                    if args.debug:
                        print(
                            f"Output file name: {out_name.with_suffix(edm4hep_file_suffix)}"
                        )

                    # Define the DDSim executable and arguments for this detector & part file
                    executable = "ddsim"
                    arguments = [
                        "--steeringFile",
                        str(
                            beamstrahlung_code_dir / "ddsim_keep_microcurlers_10MeV.py"
                        ),
                        "--compactFile",
                        str(k4geoDir / det_mod_configs.get_compact_file_path()),
                        "--inputFile",
                        str(part_file),
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
