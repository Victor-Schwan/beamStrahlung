import argparse
from dataclasses import dataclass
from os import fspath
from pathlib import Path
from typing import Dict, List, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import uproot

from vicbib import BasePlotter

save_plots = True
show_plts = False

inputFileDefault = (
    Path.home()
    / "promotion/data/TEST_IMPROVED/ILD_FCCee_v01"
    / "pairs-2_ZHatIP_tpcTimeKeepMC_keep_microcurlers_10MeV_30mrad_ILD_FCCee_v01.emd4hep.root"
)


# Define the dataclass
@dataclass
class Collection:
    branch_name: str
    plot_name: str


sub_det_cols = {
    "vb": Collection(branch_name="VertexBarrelCollection", plot_name="Vertex Barrel"),
    "ve": Collection(branch_name="VertexEndcapCollection", plot_name="Vertex Endcap"),
}

key_mapping = {
    ".position.x": "x",
    ".position.y": "y",
    ".position.z": "z",
}


def getArgumentNameSpace() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputFiles",
        "-f",
        default=fspath(inputFileDefault),
        type=str,
        nargs="+",
        help="relative path to the input file",
    )
    return parser.parse_args()


def getPositionsAndTime(
    input_file: str,
) -> Tuple[Dict[str, Dict[str, np.ndarray]], Dict[str, np.ndarray]]:
    pos = {}
    time = {}
    with uproot.open(input_file + ":events") as events:
        for sub_det_key, sub_det_name in sub_det_cols.items():
            branch_base_name = sub_det_name.branch_name + "/" + sub_det_name.branch_name
            iter_cols = iter(key_mapping)
            pos[sub_det_key] = events.arrays(
                [
                    branch_base_name + next(iter_cols),
                    branch_base_name + next(iter_cols),
                    branch_base_name + next(iter_cols),
                ],
                library="np",
            )
            time[sub_det_key] = events[
                "VertexBarrelCollection/VertexBarrelCollection.time"
            ].array(library="np")
            # Renaming keys in place
            for old_key, new_key in key_mapping.items():
                pos[sub_det_key][new_key] = pos[sub_det_key].pop(
                    branch_base_name + old_key
                )

            # Flatten the arrays
            pos[sub_det_key] = flatten_first_entry(pos[sub_det_key])
            time[sub_det_key] = flatten_first_entry(time[sub_det_key])
    return pos, time


def calculate_histograms_pos_z(
    pos: Dict[str, Dict[str, np.ndarray]]
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    histograms = {}
    for sub_det_key in sub_det_cols.keys():
        counts, edges = np.histogram(pos[sub_det_key]["z"], bins=50)
        histograms[sub_det_key] = (counts, edges)
    return histograms


def calculate_histograms_pos_z_multiple_files(
    pos_list: List[Dict[str, Dict[str, np.ndarray]]],
    sub_det_cols: Dict[str, str],
    bins: int = 50,
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    This function takes in a list of dictionaries (pos_list), where each dictionary corresponds to one file.
    It accumulates the histogram counts and edges for each sub-detector across all files.

    Args:
    pos_list: A list of dictionaries where each dictionary corresponds to a file's data.
              Each dictionary contains sub-detector keys and arrays for 'z' positions.
    sub_det_cols: A dictionary that defines the sub-detectors.
    bins: Number of bins for the histogram (default: 50)

    Returns:
    A dictionary where each key corresponds to a sub-detector.
    The value is a tuple of two arrays:
        - counts_array: a 2D array with dimensions (file_index, bin_counts)
        - edges_array: a 2D array with dimensions (file_index, bin_edges)
    """

    # Initialize a dictionary to hold histogram data for all files
    histograms = {}

    # For each sub-detector key, initialize lists to hold histograms for all files
    for sub_det_key in sub_det_cols.keys():
        counts_list = []
        edges_list = []

        # Loop over each file's position data in the list
        for pos in pos_list:
            counts, edges = np.histogram(pos[sub_det_key]["z"], bins=bins)
            counts_list.append(counts)
            edges_list.append(edges)

        # Convert lists of arrays to 2D numpy arrays, where each row corresponds to one file
        histograms[sub_det_key] = (np.array(counts_list), np.array(edges_list))

    return histograms


def calculate_statistics(
    histograms: Dict[str, Tuple[np.ndarray, np.ndarray]]
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Calculate the mean and standard deviation of the histogram counts across the file index.

    Args:
    histograms: A dictionary where each key is a sub-detector, and the value is a tuple of:
                - counts_array: a 2D numpy array (files, bins)
                - edges_array: a 2D numpy array (files, bins+1)

    Returns:
    A dictionary where each key is a sub-detector, and the value is a tuple of:
        - mean_counts: The mean counts across files for each bin.
        - std_counts: The standard deviation of the counts across files for each bin.
        - mean_edges: The mean of the edges across files (for completeness, although edges are generally the same across files).
    """

    statistics = {}

    for sub_det_key, (counts_array, edges_array) in histograms.items():
        # Mean and standard deviation of histogram counts over files
        mean_counts = np.mean(counts_array, axis=0)
        std_counts = np.std(counts_array, axis=0)

        # Mean of histogram edges over files (typically they should be the same for all files)
        mean_edges = np.mean(edges_array, axis=0)

        # Store results
        statistics[sub_det_key] = (mean_counts, std_counts, mean_edges)

    return statistics


def plot_histogram_with_error_bars(
    mean_counts: np.ndarray,
    std_counts: np.ndarray,
    mean_edges: np.ndarray,
    title: str = "Histogram with Mean and Standard Deviation",
    xlabel: str = "Bins",
    ylabel: str = "Counts",
):
    """
    Plots the mean counts with error bars representing the standard deviation.

    Args:
    mean_counts: The mean counts for each bin (1D array).
    std_counts: The standard deviation of the counts for each bin (1D array).
    mean_edges: The mean bin edges (1D array, size = bins + 1).
    title: Title of the plot (default: "Histogram with Mean and Standard Deviation").
    xlabel: Label for the x-axis (default: "Bins").
    ylabel: Label for the y-axis (default: "Counts").
    """

    # Calculate the bin centers from the edges
    bin_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot the mean counts as bars
    ax.bar(
        bin_centers,
        mean_counts,
        width=mean_edges[1] - mean_edges[0],
        alpha=0.7,
        label="Mean Counts",
    )

    # Add error bars to represent the standard deviation
    ax.errorbar(
        bin_centers,
        mean_counts,
        yerr=std_counts,
        fmt="o",
        color="red",
        label="Standard Deviation",
    )

    # Set the title and labels
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Add a legend
    ax.legend()

    # Display the plot
    plt.show()


def plotting(
    pos: Dict[str, Dict[str, np.ndarray]],
    time: Dict[str, np.ndarray],
    show_plots: bool = True,
) -> None:

    for sub_det_key, sub_det_name in sub_det_cols.items():

        bp = BasePlotter(
            save_plots, sub_det_name.plot_name.replace(" ", "_") + "_z_positions"
        )
        _, ax = bp.plot()
        # Plot histogram of the z positions
        ax.hist(pos[sub_det_key]["z"], bins=50)
        ax.set_title(f"Z Positions in {sub_det_name.plot_name}")
        ax.set_xlabel("Z Position in mm")
        ax.set_ylabel("Frequency")
        if show_plots:
            plt.show()
        bp.finish()

        # Plot histogram of the times using BasePlotter
        bp = BasePlotter(
            save_plots, sub_det_name.plot_name.replace(" ", "_") + "_hit_times"
        )
        _, ax = bp.plot()
        ax.hist(time[sub_det_key], bins=30)
        ax.set_title(f"Hit Time in {sub_det_name.plot_name}")
        ax.set_xlabel("Time in ns")
        ax.set_ylabel("Frequency")
        if show_plots:
            plt.show()
        bp.finish()

        # Plot 2D histogram of the x and y positions using BasePlotter
        bp = BasePlotter(
            save_plots, sub_det_name.plot_name.replace(" ", "_") + "_xy_hist"
        )
        fig, ax = bp.plot()
        h = ax.hist2d(
            pos[sub_det_key]["x"], pos[sub_det_key]["y"], bins=50, cmap="viridis"
        )
        ax.set_title(f"X and Y Positions in {sub_det_name.plot_name}")
        ax.set_xlabel("X Position in mm")
        ax.set_ylabel("Y Position in mm")
        fig.colorbar(
            h[3], ax=ax, label="Counts"
        )  # Add a colorbar to the figure, linked to the histogram
        if show_plots:
            plt.show()
        bp.finish()


def flatten_first_entry(
    data: Union[Dict[str, np.ndarray], np.ndarray]
) -> Union[Dict[str, np.ndarray], np.ndarray]:
    """
    Replace each array of arrays with the first nested array.

    Parameters:
    - data (dict or np.ndarray): A dictionary with numpy arrays or a single numpy array.

    Returns:
    - A new dictionary or numpy array with the first nested arrays.
    """
    if isinstance(data, dict):
        # Handle the case for dictionaries like pos
        flattened_data = {}
        for key, value in data.items():
            if (
                isinstance(value, np.ndarray)
                and value[0].shape[0] > 0
                and value[1].shape[0] == 0
            ):
                # Check if it's indeed an array of arrays and non-empty
                flattened_data[key] = value[0]
            else:
                flattened_data[key] = value
        return flattened_data
    if isinstance(data, np.ndarray) and data.ndim > 1 and data.shape[0] > 0:
        # Handle the case for numpy arrays like vbc_time if similar structure
        return data[0]
    return data


def main() -> None:

    args = getArgumentNameSpace()
    pos_list = []
    time_list = []
    for input_file in args.inputFiles:
        pos, time = getPositionsAndTime(input_file)
        pos_list.append(pos)
        time_list.append(time)
    pos_hists = calculate_histograms_pos_z_multiple_files(pos_list, sub_det_cols)
    pos_stats = calculate_statistics(pos_hists)
    plot_histogram_with_error_bars(
        *pos_stats[next(iter(sub_det_cols.keys()))],
        title=list(sub_det_cols.values())[0].plot_name,
        xlabel="Z Positions",
        ylabel="Counts",
    )

    plotting(pos, time, show_plts)


main()
