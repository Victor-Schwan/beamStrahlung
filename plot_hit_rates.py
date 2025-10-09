import matplotlib.pyplot as plt
import numpy as np

from get_subdet_params import get_params

params = get_params()

scenarios = {
    "182GeV_nzco_10urad": {
        "label": "SR Core (Scaled)",
        "bx_rate": 50000000.0,
        "c": "b",
    },
    "FCC091": {
        "label": "FCC091",
        "bx_rate": 50000000.0,
        "c": "g",
    },
    "FCC240": {
        "label": "FCC240",
        "bx_rate": 50000000.0,
        "c": "orange",
    },
    "ILC250": {
        "label": "ILC250",
        "bx_rate": 6600.0,
        "c": "purple",
    },
    "182GeV_halo": {
        "label": "SR Halo (Scaled)",
        "bx_rate": 50000000.0,
        "c": "brown",
    },
}


def extract_values(rows, det_mod, subdet, scenario):
    # Keep only rows with correct detector, subdetector, and containing the scenario
    filtered = [
        row
        for row in rows
        if row.get("Detector Model") == det_mod
        and row.get("Subdetector") == subdet
        and scenario in row.keys()
    ]

    # Sort by layer
    filtered_sorted = sorted(filtered, key=lambda r: r.get("layer", float("inf")))

    # Convert scenario values to floats (in case they are stored as strings like " 1.23e+04")
    values = [float(row[scenario]) for row in filtered_sorted]

    return np.array(values, dtype=float)


def plot_endcap(rows, axes, det_mod):
    z_positions = params[det_mod]["Vertex"]["ve"]["z"]
    axes.set_xlabel("Endcap Layer z position (mm)", fontsize=16)
    axes.set_xlim(min(z_positions) - 5, max(z_positions) + 5)
    axes.set_xticks(z_positions[0::2])
    axes.set_title(det_mod + " VXD endcap", fontsize=22)
    for scenario in scenarios.keys():
        dict = scenarios[scenario]
        hit_rates = extract_values(rows, det_mod, "Vertex", scenario)[6:]
        if len(hit_rates) == len(z_positions):
            axes.plot(
                z_positions,
                hit_rates * dict["bx_rate"],
                marker=".",
                label=dict["label"],
                c=dict["c"],
            )


def plot_barrel(rows, axes, det_mod):
    radii = params[det_mod]["Vertex"]["vb"]["r"]
    axes.set_xlabel("Barrel Layer Radius (mm)", fontsize=16)
    axes.set_xlim(10, 62)
    axes.set_xticks(radii[0::2])
    axes.set_title(det_mod + " VXD barrel", fontsize=22)
    for scenario in scenarios.keys():
        dict = scenarios[scenario]
        hit_rates = extract_values(rows, det_mod, "Vertex", scenario)[:6]
        if len(hit_rates) == len(radii):
            axes.plot(
                radii,
                hit_rates * dict["bx_rate"],
                marker=".",
                label=dict["label"],
                c=dict["c"],
            )


def plot_hit_rates(rows):
    fig = plt.figure(figsize=(12, 6))
    axes = fig.subplots(1, 3)
    plot_endcap(rows, axes[0], "ILD_FCCee_v01")
    plot_barrel(rows, axes[1], "ILD_FCCee_v01")
    plot_barrel(rows, axes[2], "ILD_l5_v02")

    for ax in axes:
        ax.set_yscale("log")
        ax.set_ylim(5, 5e12)
        ax.grid()
        ax.axhline(1600 * 5e7, ls="dashed", c="red", label="100% Occupancy")
        ax.set_ylabel(r"Hit Rate (Hz/mm$^2$)", fontsize=16)
    # Collect legend handles/labels from the last axis (they're the same for both)
    handles, labels = axes[-2].get_legend_handles_labels()

    # Place legend centered below the plots
    fig.legend(handles, labels, loc="lower center", ncol=3, framealpha=0, fontsize=14)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)  # make space for legend
    plt.show()
