import argparse
import json
import os
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from get_hits_per_layer import divide_hits
from plot_hit_rates import plot_hit_rates
from scale_hit_rate import scale_hits_dict

json_data_folder_name = "json_data"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Creates Table of hit rate for different detector models, scenarios and backgrounds"
    )
    parser.add_argument(
        "--version",
        "--directory",
        required=True,
        type=str,
        help="Version name / Directory containing the json_data directory; can be relative to the 'dtDir' env var",
    )
    parser.add_argument(
        "--unit",
        type=str,
        default="occupancy",
        choices=("per_bx", "per_bx_per_mm", "occupancy"),
        help="The units the values in the table will be given in. Occupancy values are given as percentages",
    )
    parser.add_argument(
        "--plot_all",
        action="store_true",
        help="If given, results are plotted for beamstrahlung and synchrotron radiation. Currently only coded for unit option per_bx_per_mm.",
    )
    parser.add_argument(
        "--single_plot",
        action="store_true",
        help="If set, only a single summary plot is produced. Otherwise, multiple detailed plots are generated.",
    )
    return parser.parse_args()


args = parse_arguments()

dt_dir = os.environ[
    "dtDir"
]  # Raises KeyError if not set — use .get() if you want a fallback

# Construct the json_dir path
json_dirs = [
    Path(dt_dir) / "sim" / args.version / json_data_folder_name,
]


def extract_hits_per_bx(json_path):
    with open(json_path) as f:
        data = json.load(f)

    num_bx = data["num_bunch_crossings"]
    det_mod = data["detector_model"]
    scenario = data["scenario"]
    background = data["background"]
    hits = data["hits"]
    divided_hits = divide_hits(hits, det_mod)
    divided_hits.pop("TPC", None)
    results_dict = scale_hits_dict(divided_hits, scenario, background, num_bx, det_mod)[
        args.unit
    ]

    return det_mod, scenario, results_dict


def create_table():
    json_files = []
    for d in json_dirs:
        json_files.extend(d.glob("*.json"))

    # If you want them in a single Path list (not nested)
    json_files = list(json_files)

    rows = []

    for json_file in json_files:
        det_mod, scenario, hits = extract_hits_per_bx(json_file)
        for subdet, subdet_hits in hits.items():
            for layer, value in subdet_hits.items():
                formated_value = f" {value:.2e}"
                rows.append(
                    {
                        "Detector Model": det_mod,
                        "Subdetector": subdet,
                        "layer": layer,
                        "Background": args.version,
                        scenario: value,
                    }
                )
    if args.plot_all and args.unit == "per_bx_per_mm":
        plot_hit_rates(rows, single_plot=args.single_plot)
    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Pivot so each scenario is a separate column
    df = df.pivot_table(
        index=["Detector Model", "Subdetector", "layer", "Background"], aggfunc="first"
    ).reset_index()

    # Sort the table for clarity
    df = df.sort_values(by=["Detector Model", "Subdetector", "Background"])

    if args.version == "synchrotron":
        first_three = df.columns[:4]  # keep first 3 as-is
        reorder_rest = [
            "45GeV_halo",
            "182GeV_halo",
            "182GeV_nzco_2urad",
            "182GeV_nzco_6urad",
            "182GeV_nzco_10urad",
        ]

        df = df[list(first_three) + reorder_rest]

    return df


def main():
    df = create_table()

    # print(tabulate(df, headers="keys", tablefmt="grid"))

    latex_table = tabulate(df, headers="keys", tablefmt="latex")
    with open(json_dirs[0].parent / "background_table.tex", "w") as f:
        f.write(latex_table)
    markdown_table = tabulate(df, headers="keys", tablefmt="github")
    print(markdown_table)


if __name__ == "__main__":
    main()
