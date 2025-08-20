import json
from pathlib import Path
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

def scale_sr_hits(n_hits, scenario):
    with open(path_to_v23_reference) as f:
        parameters = json.load(f)
    
    energy, component = scenario.split("_")[:2]
    simulated_population = simulated_populations[scenario]
    bunch_population = parameters[energy_labels[energy]]["BUNCH_POPULATION"]

    scaled_n_hits = n_hits * bunch_population * bunch_fraction[component] / simulated_population 

    return scaled_n_hits