import json
from pathlib import Path

from get_subdet_params import get_params
from platform_paths import resolve_path_with_env

path_to_v23_reference = resolve_path_with_env(
    Path("fcc-ee-lattice/reference_parameters.json"), "codeDir"
)

# the halo populations were taken from the full filenames. The nzco were taken from
simulated_populations = {
    "182GeV_nzco_10urad": 5e6,
    "182GeV_nzco_6urad": 5e6,
    "182GeV_nzco_2urad": 5e6,
    "182GeV_halo": 8e7,
    "45GeV_nzco_10urad": 1e7,
    "45GeV_nzco_6urad": 1e7,
    "45GeV_nzco_2urad": 1e7,
    "45GeV_halo": 2e7,
}

energy_labels = {
    "182GeV": "t",
    "45GeV": "z",
}

bunch_fraction = {
    "halo": 0.01,
    "nzco": 0.99,
}


def scale_sr_hits(n_hits, scenario, background="synchrotron", num_bx=1):
    if background != "synchrotron":
        return n_hits / num_bx

    with open(path_to_v23_reference) as f:
        parameters = json.load(f)

    energy, component = scenario.split("_")[:2]
    simulated_population = simulated_populations[scenario]
    bunch_population = parameters[energy_labels[energy]]["BUNCH_POPULATION"]

    scaled_n_hits = (
        n_hits * bunch_population * bunch_fraction[component] / simulated_population
    )

    return scaled_n_hits / num_bx


def scale_hits_dict(divided_hits, scenario, background, num_bx, det_mod):
    det_params = get_params()[det_mod]

    # calls above function and does simple scaling to fix 2 things
    #    1) scale up to real particle population
    #    2) divide by n_BX
    hit_rates = {
        subdet: {
            layer: scale_sr_hits(len(hits["z"]), scenario, background, num_bx)
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in divided_hits.items()
    }

    # takes above scaled hits and further divides by area of subdetector
    hit_rates_per_mm = {
        subdet: {
            layer: hits / det_params[subdet][layer.split("_")[0]]["a"][int(layer.split("_")[1])-1]
            # e.g.: det_params['Vertex']['vb_1'.split("_")[0]='vb']["a"][layer.split("_")[1]-1='0']
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in hit_rates.items()
    }

    # takes "per_bx" scaling but without area divison and divides by number of pixels
    occupancy = {
        subdet: {
            layer: 100 * hits / det_params[subdet][layer.split("_")[0]]["n_pixels"][int(layer.split("_")[1])-1]
            # 100 to convert to percent
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in hit_rates.items()
    }

    results_dict = {
        "per_bx": hit_rates,
        "per_bx_per_mm": hit_rates_per_mm,
        "occupancy": occupancy,
    }

    return results_dict
