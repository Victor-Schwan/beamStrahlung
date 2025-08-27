import json
from pathlib import Path
from get_areas import get_params
import numpy as np

path_to_v23_reference = Path("../fcc-ee-lattice/reference_parameters.json")

# vertex_pixel_size taken from 'CLD - A Detector Concept for the FCC-ee'. Could not locate in k4Geo (potential violation of single source of truth)
vertex_pixel_size = 0.025 # mm

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

def scale_sr_hits(n_hits, scenario, background="synchrotron"):
    if background != "synchrotron":
        return n_hits

    with open(path_to_v23_reference) as f:
        parameters = json.load(f)
    
    energy, component = scenario.split("_")[:2]
    simulated_population = simulated_populations[scenario]
    bunch_population = parameters[energy_labels[energy]]["BUNCH_POPULATION"]

    scaled_n_hits = n_hits * bunch_population * bunch_fraction[component] / simulated_population 

    return scaled_n_hits

def scale_vb_hits(z, scenario, background, num_bx, subdet_params, layer_index):
    half_length = subdet_params["z"][layer_index]

    bin_width_pixels = 120

    num_bins = int(2 * half_length / (vertex_pixel_size * bin_width_pixels))

    counts = np.histogram(z, num_bins)[0] / num_bx

    scaled_hit_rate = 0

    num_pixels = int(subdet_params["a"][layer_index] / num_bins / vertex_pixel_size**2)

    for count in counts:
        scaled_count = scale_sr_hits(count, scenario, background)

        if scaled_count < 0.05 * num_pixels or scaled_count < 1:
            scaled_hit_rate += scaled_count
            continue

        int_count = int(scaled_count)

        decimal_count = scaled_count - int_count

        hit_pixels = np.random.randint(0,  num_pixels, size=int_count)

        num_hit_pixels = len(np.unique(hit_pixels))

        scaled_hit_rate += num_hit_pixels + decimal_count

    return scaled_hit_rate

def scale_ve_hits(z, scenario, background, num_bx, subdet_params, layer_index):

    num_pixels = int(subdet_params["a"][layer_index] / (vertex_pixel_size**2))

    scaled_count = scale_sr_hits(len(z)/num_bx, scenario, background)

    if scaled_count < 0.05 * num_pixels or scaled_count < 1:
        scaled_hit_rate = scaled_count

    else:
        int_count = int(scaled_count)
        decimal_count = scaled_count - int_count

        hit_pixels = np.random.randint(0,  num_pixels, size=int_count)
        num_hit_pixels = len(np.unique(hit_pixels))

        scaled_hit_rate = num_hit_pixels + decimal_count

    return scaled_hit_rate

scaling_functions = {
    "vb": scale_vb_hits,
    "ve": scale_ve_hits,
}

def scale_hits_dict(divided_hits, scenario, background, num_bx, det_mod):
    
    det_params = get_params()[det_mod]

    hit_rates = {
        layer: (
            scaling_functions[layer.split("_")[0]](hits["z"], scenario, background, num_bx, det_params[layer.split("_")[0]], int(layer.split("_")[1])-1)
        )
        for layer, hits in divided_hits.items()
    }

    results_dict = {
         "per_bx": hit_rates,
         "per_bx_per_mm": {layer: hit_rate / det_params[layer.split("_")[0]]["a"][int(layer.split("_")[1])-1] for layer, hit_rate in hit_rates.items()},
         "occupancy": {layer: 100 * hit_rate / det_params[layer.split("_")[0]]["a"][int(layer.split("_")[1])-1] * 
                       vertex_pixel_size**2 for layer, hit_rate in hit_rates.items()},
    }

    return results_dict