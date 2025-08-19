import argparse
import json
import os
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from get_areas import get_areas

subdetector_labels = {
    "vb": "vertex barrel",
    "ve": "vertex endcap",
}
subdetector_areas = get_areas()


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
    return parser.parse_args()


args = parse_arguments()

dt_dir = os.environ[
    "dtDir"
]  # Raises KeyError if not set — use .get() if you want a fallback

# Construct the json_dir path
json_dir = Path(dt_dir) / args.version / "json_data"


def extract_hits_per_bx(json_path):
    with open(json_path) as f:
        data = json.load(f)

    num_bx = data["num_bunch_crossings"]
    det_mod = data["detector_model"]
    scenario = data["scenario"]

    hits_dict = {}

    for subdet, pos_data in data["pos"].items():
        if subdet == "f":
            continue
        n_hits = len(pos_data["x"])
        label = subdetector_labels.get(subdet, subdet)
        if det_mod == "ILD_l5_v02":
            num_bx *= 42 * 5000 / 162616
        hits_dict[label] = n_hits / num_bx / subdetector_areas[det_mod][subdet]

    return det_mod, scenario, hits_dict


def create_table():
    json_files = list(json_dir.glob("*.json"))

    rows = []

    for json_file in json_files:
        det_mod, scenario, hits = extract_hits_per_bx(json_file)
        for label, value in hits.items():
            formated_value = f" {value:.10e}"
            rows.append(
                {
                    "Detector Model": det_mod,
                    "Subdetector": label,
                    "Background": args.version,
                    scenario: formated_value,
                }
            )

    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Pivot so each scenario is a separate column
    df = df.pivot_table(
        index=["Detector Model", "Subdetector", "Background"], aggfunc="first"
    ).reset_index()

    # Sort the table for clarity
    df = df.sort_values(by=["Detector Model", "Subdetector", "Background"])

    if args.version == "synchrotron":
        desired_order = [
            "Detector Model",
            "Subdetector",
            "Background",
            "10urad_nzco",
            "6urad_nzco",
            "2urad_nzco",
            "45GeV_halo",
            "182GeV_halo",
        ]
        df = df[desired_order]

    return df


def main():
    df = create_table()

    print(tabulate(df, headers="keys", tablefmt="grid"))

    latex_table = tabulate(df, headers="keys", tablefmt="latex")
    with open(json_dir / "../background_table.tex", "w") as f:
        f.write(latex_table)
    markdown_table = tabulate(df, headers="keys", tablefmt="github")
    print(markdown_table)


if __name__ == "__main__":
    main()
