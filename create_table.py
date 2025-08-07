import json
from tabulate import tabulate
from get_areas import get_areas

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
def extract_hits_per_bx(json_path):
    with open(json_path) as f:
        data = json.load(f)

    num_bx = data["num_bunch_crossings"]
    det_mod = data["detector_model"]
    scenario = "Hits / BX / mm^2\n"+data["scenario"]

    hits_dict = {}

    for subdet, pos_data in data["positions"].items():
        n_hits = len(pos_data["x"])
        label = subdetector_labels.get(subdet, subdet)
        hits_dict[label] = n_hits / num_bx / subdetector_areas[subdet]

    return det_mod, scenario, data["background"], hits_dict

def create_table(json_dir=jsonDir):
    from pathlib import Path
    import pandas as pd

    json_dir = Path(json_dir)
    json_files = list(json_dir.glob("*.json"))

    rows = []

    for json_file in json_files:
        det_mod, scenario, background, hits = extract_hits_per_bx(json_file)
        for label, value in hits.items():
            rows.append({
                "Detector Model": det_mod,
                "Subdetector": label,
                "Background": background,
                scenario: value
            })

    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Pivot so each scenario is a separate column
    df = df.pivot_table(
        index=["Detector Model", "Subdetector", "Background"],
        aggfunc="first"
    ).reset_index()

    # Sort the table for clarity
    df = df.sort_values(by=["Detector Model", "Subdetector"])

    return df


def main():
    df = create_table()

    print(tabulate(df, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    main()
