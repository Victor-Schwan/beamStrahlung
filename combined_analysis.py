import argparse
from os import fspath
from pathlib import Path

from tabulate import tabulate

from analyze_available_data import parse_files, print_detector_info, sort_detector_data
from caching import handle_cache_operations
from det_mod_configs import (
    CHOICES_DETECTOR_MODELS,
    DEFAULT_DETECTOR_MODELS,
)
from platform_paths import (
    SIM_DATA_SUBDIR_NAME,
    edm4hep_file_suffix,
    get_home_directory,
    resolve_path_with_env,
)
from plotting import plotting
from simall import CHOICES_SCENARIOS, DEFAULT_SCENARIOS

show_plts = False
SIM_DATA_SUBDIR_NAME = ""


def parse_arguments():
    homeDir = get_home_directory()

    parser = argparse.ArgumentParser(
        description="Combined Analysis of Detector Model Files"
    )
    parser.add_argument(
        "--version",
        "--directory",
        required=True,
        type=str,
        help="Version name / Directory containing the data files; can be relative to the 'dtDir' env var",
    )
    parser.add_argument(
        "--mode",
        default="overview",
        choices=["overview", "analysis", "ana_all"],
        help="Mode of operation: overview, analysis, or ana_all",
    )
    parser.add_argument(
        "--detectorModel",
        choices=CHOICES_DETECTOR_MODELS,
        nargs="+",
        default=DEFAULT_DETECTOR_MODELS,
        type=str,
        help="Specify one or more detector models for analysis",
    )
    parser.add_argument(
        "--scenario",
        nargs="+",
        type=str,
        choices=CHOICES_SCENARIOS,
        default=DEFAULT_SCENARIOS,
        help="Specify one or more scenarios for analysis",
    )
    parser.add_argument(
        "--cacheDir",
        default=fspath(homeDir / "promotion/data/bs_cache_combined_analysis"),
        type=str,
        help="Directory to store cache files",
    )
    parser.add_argument(
        "--savePlots", action="store_true", help="If given, plots are stored."
    )

    return parser.parse_args()


def analyze_combination(directory, detector_model, scenario, detector_data, args):
    """Analyze a specific combination of detector model and scenario."""

    if (
        detector_model not in detector_data
        or scenario not in detector_data[detector_model]
    ):
        raise ValueError(
            f"No files found for the combination: Detector Model='{detector_model}', Scenario='{scenario}'"
        )

    # Get the list of bX identifiers (bunch crossing identifiers)
    bX_identifiers = detector_data[detector_model][scenario]

    # Determine the number of bunch crossings
    num_bX = len(bX_identifiers)

    # Prepare file paths
    file_paths = [
        fspath(p)
        for bX_identifier in bX_identifiers
        for p in directory.glob(
            f"{detector_model}-{scenario}-{bX_identifier}-nEvts_*{edm4hep_file_suffix}"
        )
    ]

    # Print current combination in a grid table format
    table_data = [[detector_model, scenario, num_bX]]
    print(
        tabulate(
            table_data,
            headers=["Detector Model", "Scenario", "Num Bunch Crossings"],
            tablefmt="grid",
        )
    )

    # Get the position and time arrays including caching operations
    pos, time = handle_cache_operations(
        args.cacheDir, detector_model, scenario, num_bX, file_paths
    )

    plotting(
        pos,
        time,
        num_bX,  # Pass the number of bunch crossings
        show_plts,
        save_plots=args.savePlots,
        save_dir=directory / "bp_plots",
        make_theta_hist=True,
        scenario=scenario,
        det_mod=detector_model,
    )


def main():
    args = parse_arguments()

    # if only version name provided, expanded the path based on 'dtDir' var
    directory = resolve_path_with_env(
        Path(SIM_DATA_SUBDIR_NAME) / args.version, "dtDir"
    )
    print(directory)

    # Parse the files to gather detector data and sort the keys
    parsed_data = parse_files(directory)
    detector_data = sort_detector_data(parsed_data)

    if args.mode == "overview":
        print_detector_info(detector_data)
    elif args.mode == "analysis":
        # Determine which detector models and scenarios to analyze
        detector_models = args.detectorModel or DEFAULT_DETECTOR_MODELS
        scenarios = args.scenario or DEFAULT_SCENARIOS
        assert not isinstance(detector_models, str) and not isinstance(scenarios, str)

        for detector_model in detector_models:
            if detector_model in detector_data:
                for scenario in scenarios:
                    if scenario in detector_data[detector_model]:
                        analyze_combination(
                            directory, detector_model, scenario, detector_data, args
                        )

    elif args.mode == "ana_all":
        # Analyze all combinations of detector models and scenarios
        for detector_model, scenario_list in detector_data.items():
            for scenario in scenario_list.keys():
                analyze_combination(
                    directory, detector_model, scenario, detector_data, args
                )


if __name__ == "__main__":
    main()
