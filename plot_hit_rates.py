from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np

from get_subdet_params import get_params
from platform_paths import resolve_path_with_env

bx_rate_FCC_Z = 40e6  # 40MHz
bx_rate_FCC_tt = 0.2e6  # 0.2MHz
out_plot_dir = resolve_path_with_env("2026-01-plots", "dtDir")

my_label_size = 16
my_title_font_size = 18
my_plot_params = {
    "legend.fontsize": my_label_size,
    "xtick.labelsize": my_label_size,
    "ytick.labelsize": my_label_size,
    "axes.labelsize": my_label_size,
    "axes.titlesize": my_label_size,
}
mpl.rcParams.update(my_plot_params)

params = get_params()

scenarios = {
    "182GeV_nzco_10urad": {
        "label": "SR tt Core 10urad",
        "bx_rate": bx_rate_FCC_tt,
    },
    "45GeV_nzco_10urad": {
        "label": "SR Z Core 10urad",
        "bx_rate": bx_rate_FCC_Z,
    },
    "182GeV_nzco_6urad": {
        "label": "SR tt Core 6urad",
        "bx_rate": bx_rate_FCC_tt,
    },
    "45GeV_nzco_6urad": {
        "label": "SR Z Core 6urad",
        "bx_rate": bx_rate_FCC_Z,
    },
    "182GeV_nzco_2urad": {
        "label": "SR tt Core 2urad",
        "bx_rate": bx_rate_FCC_tt,
    },
    "45GeV_nzco_2urad": {
        "label": "SR Z Core 2urad",
        "bx_rate": bx_rate_FCC_Z,
    },
    "45GeV_halo": {
        "label": "SR Z Halo",
        "bx_rate": bx_rate_FCC_Z,
    },
    "182GeV_halo": {
        "label": "SR tt Halo",
        "bx_rate": bx_rate_FCC_tt,
    },
    #    "ILC250": {
    #        "label": "ILC250",
    #        "bx_rate": 6600.0,
    #    },
}

# ensure an unambigious color-scenario mapping
cmap = cm.get_cmap("tab10")
scenario_colors = {scenario: cmap(i) for i, scenario in enumerate(scenarios)}


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
    axes.set_title(det_mod + " VXD endcap", fontsize=my_title_font_size)
    for scenario in scenarios.keys():
        plot_para_dict = scenarios[scenario]
        hit_rates = extract_values(rows, det_mod, "Vertex", scenario)[6:]
        if len(hit_rates) == len(z_positions):
            axes.plot(
                z_positions,
                hit_rates,
                marker=".",
                label=plot_para_dict["label"],
                color=scenario_colors[scenario],
            )


def plot_barrel(rows, axes, det_mod):
    radii = params[det_mod]["Vertex"]["vb"]["r"]
    axes.set_xlabel("Barrel Layer Radius (mm)", fontsize=16)
    axes.set_xlim(10, 62)
    axes.set_xticks(radii[0::2])
    axes.set_title(det_mod + " VXD barrel", fontsize=my_title_font_size)
    for scenario in scenarios.keys():
        plot_para_dict = scenarios[scenario]
        hit_rates = extract_values(rows, det_mod, "Vertex", scenario)[:6]
        if len(hit_rates) == len(radii):
            axes.plot(
                radii,
                hit_rates,
                marker=".",
                label=plot_para_dict["label"],
                color=scenario_colors[scenario],
            )


def plot_hit_rates(rows):
    fig = plt.figure(figsize=(12, 6), constrained_layout=True)
    axes = fig.subplots(1, 3)
    plot_endcap(rows, axes[0], "ILD_FCCee_v01")
    plot_barrel(rows, axes[1], "ILD_FCCee_v01")
    plot_barrel(rows, axes[2], "ILD_l5_v02")

    for ax in axes:
        ax.set_yscale("log")
        ax.set_ylim(1, 5e5)
        ax.grid()
        ax.set_ylabel(r"Hits [1/(BX*mm$^2$)]", fontsize=16)

    # Collect legend handles/labels from the last axis (they're the same for both)
    handles, labels = axes[-2].get_legend_handles_labels()

    # Place legend centered below the plots
    fig.legend(
        handles,
        labels,
        loc="outside lower center",
        ncol=3,
        framealpha=0,
        fontsize=14,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = out_plot_dir / f"hit_rates_{timestamp}.png"
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")
