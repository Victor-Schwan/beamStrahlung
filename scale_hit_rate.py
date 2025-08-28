import json
from pathlib import Path
from get_subdet_params import get_params

path_to_v23_reference = Path("../fcc-ee-lattice/reference_parameters.json")

# the halo populations were taken from the full filenames. The nzco were taken from 
simulated_populations = { 
    "182GeV_nzco_10urad": 1e7,
    "182GeV_nzco_6urad": 1e7,
    "182GeV_nzco_2urad": 1e7,
    "45GeV_halo": 2e7,
    "182GeV_halo": 4e7,
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

    scaled_n_hits = n_hits * bunch_population * bunch_fraction[component] / simulated_population 

    return scaled_n_hits / num_bx

def scale_hits_dict(divided_hits, scenario, background, num_bx, det_mod):
    
    det_params = get_params()[det_mod]

    hit_rates = {
        subdet: {
            layer: scale_sr_hits(len(hits["z"]), scenario, background, num_bx)
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in divided_hits.items()
    }
    hit_rates_per_mm = {
        subdet: {
            layer: hits / det_params[subdet][layer.split("_")[0]]["a"][0]
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in hit_rates.items()
    }

    occupancy = {
        subdet: {
            layer: 100 * hits / det_params[subdet][layer.split("_")[0]]["n_pixels"][0]
            for layer, hits in subdet_hits.items()
        }
        for subdet, subdet_hits in hit_rates.items()
    }

    results_dict = {
        "per_bx": hit_rates,
        "per_bx_per_mm": hit_rates_per_mm,
        "occupancy": occupancy
    }

    return results_dict