import json
from tabulate import tabulate
from get_areas import get_areas
import argparse
import os
from pathlib import Path
import pandas as pd

jsonDir = "/data/dust/user/keyworth/promotion/data/sim/test/json_data"
subdetector_labels = {
    "vb": "vertex barrel",
    "ve": "vertex endcap",
}
vb_area, ve_area = get_areas()
subdetector_areas = {
    "vb": vb_area,
    "ve": ve_area,
}
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

def extract_hits_per_bx(json_path):
    with open(json_path) as f:
        data = json.load(f)

    num_bx = data["num_bunch_crossings"]
    det_mod = data["detector_model"]
    scenario = "Hits / BX / mm^2\n"+data["scenario"]

    hits_dict = {}

    for subdet, pos_data in data["pos"].items():
        n_hits = len(pos_data["x"])
        label = subdetector_labels.get(subdet, subdet)
        hits_dict[label] = n_hits / num_bx / subdetector_areas[subdet]

    return det_mod, scenario, hits_dict

def create_table():

    args = parse_arguments()

    dt_dir = os.environ["dtDir"]  # Raises KeyError if not set — use .get() if you want a fallback

    # Construct the json_dir path
    json_dir = Path(dt_dir) / args.version / "json_data"
    json_files = list(json_dir.glob("*.json"))

    rows = []

    for json_file in json_files:
        det_mod, scenario, hits = extract_hits_per_bx(json_file)
        for label, value in hits.items():
            formated_value = f" {value:.2e}"
            rows.append({
                "Detector Model": det_mod,
                "Subdetector": label,
                "Background": args.version,
                scenario: formated_value
            })

    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Pivot so each scenario is a separate column
    df = df.pivot_table(
        index=["Detector Model", "Subdetector", "Background"],
        aggfunc="first"
    ).reset_index()

    # Sort the table for clarity
    df = df.sort_values(by=["Detector Model", "Subdetector", "Background"])

    return df


def main():

    df = create_table()

    print(tabulate(df, headers="keys", tablefmt="grid"))

    latex_table = tabulate(df, headers='keys', tablefmt='latex')
    with open(jsonDir + "/../background_table.tex", "w") as f:
        f.write(latex_table)


if __name__ == "__main__":
    main()
