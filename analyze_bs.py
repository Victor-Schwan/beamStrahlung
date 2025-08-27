import argparse
from collections import defaultdict
from os import fspath
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import uproot

from det_mod_configs import detector_model_configurations
from platform_paths import edm4hep_file_suffix

save_plots = False
show_plts = True

input_file_default = (
    Path.home()
    / "promotion/data/TEST_IMPROVED/ILD_FCCee_v01"
    / "pairs-2_ZHatIP_tpcTimeKeepMC_keep_microcurlers_10MeV_30mrad_ILD_FCCee_v01"
).with_suffix(edm4hep_file_suffix)


def get_argument_name_space() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputFiles",
        "-f",
        default=fspath(input_file_default),
        type=str,
        nargs="+",
        help="relative path to the input file",
    )
    return parser.parse_args()

def get_p_n_t(
    file_paths: List[str], detector_model: str
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    pos_n_t = defaultdict(lambda: defaultdict(list))

    key_mapping = {
        ".position.x": "x",
        ".position.y": "y",
        ".position.z": "z",
        ".time": "t",
    }

    sub_det_cols = detector_model_configurations[
        detector_model
    ].get_sub_detector_collection_info()

    for sub_det_key, hit_col in sub_det_cols.items():
        alis = {
            value: f"{hit_col.root_tree_branch_name}{key}"
            for key, value in key_mapping.items()
        }

        # uproot.concatenate not used as depends on available/needed memory
        for batch in uproot.iterate(
            [{fp: "events"} for fp in file_paths],
            list(alis.keys()),
            library="np",
            aliases=alis,
        ):
            for observable_key in alis.keys():
                pos_n_t[sub_det_key][observable_key].append(batch[observable_key])

    # Flattening the dict entries
    for sub_det_key, observables in pos_n_t.items():
        for observable_key, arrays in observables.items():
            # Concatenate the arrays and flatten in case of multi-dimensional arrays
            # 1. Concatenation: due to several files and list in defaultdict
            concatenated_array = (
                np.concatenate(arrays) if len(arrays) > 1 else arrays[0]
            )
            # 2. Concatenation: due to several events in a root file resulting in nested ndarrays
            observables[observable_key] = (
                np.concatenate(concatenated_array)
                if isinstance(
                    concatenated_array[0], np.ndarray
                )  # testing only 0th entry should be fine as above concat. enforces same datatype
                else concatenated_array
            )

    return dict(pos_n_t)

def get_hits(file_paths: List[str], detector_model: str) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Returns hits as a single dictionary:
    {
        'vb': {'x': ..., 'y': ..., 'z': ..., 't': ...},
        've': {'x': ..., 'y': ..., 'z': ..., 't': ...}
    }
    """
    pos_n_t = defaultdict(lambda: defaultdict(list))

    key_mapping = {
        ".position.x": "x",
        ".position.y": "y",
        ".position.z": "z",
        ".time": "t",
    }

    sub_det_cols = detector_model_configurations[detector_model].get_sub_detector_collection_info()

    for sub_det_key, hit_col in sub_det_cols.items():
        alis = {value: f"{hit_col.root_tree_branch_name}{key}" for key, value in key_mapping.items()}

        for batch in uproot.iterate(
            [{fp: "events"} for fp in file_paths],
            list(alis.keys()),
            library="np",
            aliases=alis,
        ):
            for observable_key in alis.keys():
                pos_n_t[sub_det_key][observable_key].append(batch[observable_key])

    # Flatten arrays
    hits = {}
    for sub_det_key, observables in pos_n_t.items():
        hits[sub_det_key] = {}
        for observable_key, arrays in observables.items():
            # concatenate arrays
            concatenated_array = np.concatenate(arrays) if len(arrays) > 1 else arrays[0]
            # flatten nested arrays if needed
            if isinstance(concatenated_array[0], np.ndarray):
                concatenated_array = np.concatenate(concatenated_array)
            hits[sub_det_key][observable_key] = concatenated_array

    return hits
