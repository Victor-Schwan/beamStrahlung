import argparse
import json
from os import fspath
from pathlib import Path

import numpy as np
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
    get_path_from_env,
    resolve_path_with_env,
)
from plotting import plotting
from scenario_folder_utils import collect_all_parts
from simall import CHOICES_SCENARIOS, DEFAULT_SCENARIOS, get_args

show_plts = False


def parse_arguments():
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
        "--background",
        type=str,
        choices=CHOICES_SCENARIOS.keys(),
        help="Type of background data to read. Defaults to version if valid option or else beamstrahlung",
    )
    parser.add_argument(
        "--scenario",
        nargs="+",
        type=str,
        help="Specify one or more scenarios for analysis",
    )
    parser.add_argument(
        "--cacheDir",
        default=fspath(get_path_from_env("dtDir") / "bs_cache_combined_analysis"),
        type=str,
        help="Directory to store cache files",
    )
    parser.add_argument(
        "--savePlots", action="store_true", help="If given, plots are stored."
    )

    return parser.parse_args()


def convert_to_serializable(obj):
    """Recursively convert NumPy arrays to lists for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj


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
    bX_identifiers = detector_data[detector_model][scenario].keys()

    # Determine the number of bunch crossings
    num_bX = len(bX_identifiers)

    # Prepare file paths
    file_paths_nested = collect_all_parts(
        directory / detector_model / scenario, edm4hep_file_suffix
    )
    file_paths = [fspath(path) for lst in file_paths_nested.values() for path in lst]

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
    hits = handle_cache_operations(
        args.cacheDir, detector_model, scenario, num_bX, file_paths
    )

    # Ensure the json_data directory exists
    json_data_dir = directory / "json_data"
    json_data_dir.mkdir(parents=True, exist_ok=True)

    # Define the output JSON file path
    json_file_path = json_data_dir / f"{detector_model}_{scenario}_pos.json"

    data_to_save = {
        "detector_model": detector_model,
        "background": args.background,
        "scenario": scenario,
        "num_bunch_crossings": num_bX,
        "hits": convert_to_serializable(hits),
    }

    # Save the dictionary to a JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(data_to_save, json_file, indent=4)

    plotting(
        hits,
        num_bX,  # Pass the number of bunch crossings
        show_plts,
        save_plots=args.savePlots,
        save_dir=directory / "bp_plots",
        make_theta_hist=True,
        scenario=scenario,
        det_mod=detector_model,
        background=args.background,
    )


def main():
    args = get_args(parse_arguments)
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
