import json
from pathlib import Path
from get_areas import extract_constants
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

def get_barrel_occupancy(z, scenario, background="synchrotron", num_bx=1):

    constants = extract_constants()

    half_length = constants["VertexBarrel_zmax"][0]
    bin_width_pixels = 120

    num_bins = int(2 * half_length / (vertex_pixel_size * bin_width_pixels))

    counts = np.histogram(z, num_bins)[0] / num_bx

    scaled_hit_rate = 0

    num_pixels = int(bin_width_pixels * 2 * 2 * np.pi * sum(constants["VertexBarrel_r"]) / vertex_pixel_size)
    for i, count in enumerate(counts):
        scaled_count = scale_sr_hits(count, scenario, background)

        if scaled_count < 0.05 * num_pixels or scaled_count < 1:
            scaled_hit_rate += scaled_count
            continue

        int_count = int(scaled_count)

        decimal_count = scaled_count - int_count

        hit_pixels = np.random.randint(0,  num_pixels, size=int_count)

        num_hit_pixels = len(np.unique(hit_pixels))

        scaled_hit_rate += num_hit_pixels + decimal_count

    occupancy = scaled_hit_rate / (num_bins * num_pixels)

    return occupancy

def get_endcap_occupancy(z, scenario, background="synchrotron", num_bx=1):

    constants = extract_constants()

    radius = constants["VertexEndcap_rmax"][0]

    num_pixels = int(2 * np.pi * radius**2 * 2 * len(constants["VertexEndcap_z"]) / (vertex_pixel_size**2))

    scaled_count = scale_sr_hits(len(z), scenario, background)

    if scaled_count < 0.05 * num_pixels or scaled_count < 1:
        scaled_hit_rate = scaled_count
    else:
        int_count = int(scaled_count)
        decimal_count = scaled_count - int_count

        hit_pixels = np.random.randint(0,  num_pixels, size=int_count)
        num_hit_pixels = len(np.unique(hit_pixels))

        scaled_hit_rate = num_hit_pixels + decimal_count

    occupancy = scaled_hit_rate / num_pixels

    return occupancy