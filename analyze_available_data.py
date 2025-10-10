"""
This script analyzes detector model files following a specific naming convention.

The expected file naming format is:
DETECTOR_MODEL-SCENARIO-bX_NUMBER-nEvts_ENUMBER.edm4hep.root or
DETECTOR_MODEL_____-SCENARIO-bX_NUMBER-nEvts_ENUMBER.edm4hep.root

The script scans a directory for files that match this format, organizes the
data by detector model and scenario, and counts the number of different
bX_NUMBER files found for each scenario within each detector model.

Usage:
    python analyze_detectors.py --directory <directory>  # or -d <directory>

Arguments:
    <directory>  Path to the directory containing the detector model files.
"""

import os
from collections import defaultdict
from pathlib import Path

from tabulate import tabulate

from det_mod_configs import CHOICES_DETECTOR_MODELS


def parse_files(directory):
    """
    Parse the specified directory for files that match the expected naming format.

    The expected filename format is:
    DETECTOR_MODEL-SCENARIO-bX_NUMBER-nEvts_ENUMBER.edm4hep.root or
    DETECTOR_MODEL_____-SCENARIO-bX_NUMBER-nEvts_ENUMBER.edm4hep.root

    Parameters:
    directory (str): The directory to scan for files.

    Returns:
    defaultdict: A nested dictionary containing detector models as keys,
                 scenarios as subkeys, and sets of bX numbers as values.
    """

    detector_data = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if (
            os.path.isdir(folder_path) and folder in CHOICES_DETECTOR_MODELS
        ):  # only look at folders
            for subfolder in os.listdir(folder_path):
                bX_number = subfolder.split("_")[-1]

                subfolder_path = os.path.join(folder_path, subfolder)
                for file_path in (Path(directory) / folder / subfolder).rglob(
                    "*.edm4hep.root"
                ):
                    # Extract components of the filename
                    parts = file_path.stem.split("-")
                    if len(parts) != 5:
                        continue  # Skip any files that don't match the expected format
                    detector_model = parts[0]
                    scenario = parts[1]
                    bX_number = parts[2]
                    e_number = parts[3].split("_")[-1]
                    part = parts[4].split("_")[-1].split(".")[0]

                    # Add the bX_Number to the appropriate detector_model and scenario
                    detector_data[detector_model][scenario][bX_number].add(part)

    return detector_data


def sort_detector_data(detector_data):
    """
    Sort the detector data by detector model, scenario, and bX numbers.

    Parameters:
    detector_data (defaultdict): The nested dictionary containing detector
                                  models, scenarios, and their corresponding bX numbers.

    Returns:
    sorted_data (defaultdict): A sorted nested defaultdict.
    """
    sorted_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # Sort the detector models
    for detector_model in sorted(detector_data.keys()):
        scenarios = detector_data[detector_model]

        # Sort scenarios for the current detector model
        for scenario in sorted(scenarios.keys()):
            bX_dict = scenarios[scenario]

            # Sort bX_numbers for the current scenario
            for bX_number in sorted(bX_dict.keys()):
                # Sort the parts inside each bX_number
                sorted_parts = sorted(bX_dict[bX_number])
                sorted_data[detector_model][scenario][bX_number] = sorted_parts

    return sorted_data


def print_detector_info(sorted_detector_data):
    """
    Print a table of detector information, including models, scenarios,
    and the count of different files found for each scenario.

    Parameters:
    sorted_detector_data (defaultdict): The sorted nested dictionary containing detector
                                        models, scenarios, and their corresponding bX numbers.
    """
    table_data = []

    # Prepare the table data
    for detector_model in sorted_detector_data.keys():
        scenarios = sorted_detector_data[detector_model]

        # Iterate over the scenarios for the current detector model
        for scenario in scenarios.keys():
            bX_numbers = scenarios[scenario].keys()
            num_bX = len(bX_numbers)
            num_files = 0
            for bX in bX_numbers:
                num_files += len(scenarios[scenario][bX])
            table_data.append([detector_model, scenario, num_bX, num_files])

    # Print the table using tabulate
    print(
        tabulate(
            table_data,
            headers=["Detector Model", "Scenario", "Number of BX", "Number of Files"],
            tablefmt="grid",
        )
    )
