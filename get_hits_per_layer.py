import numpy as np
from get_areas import get_params


def divide_hits(hits, det_mod):

    vb_hits = {k: np.array(v) for k, v in hits["vb"].items()}

    det_params = get_params()[det_mod]

    vb_hit_radii = np.sqrt(np.array(vb_hits["x"])**2 + np.array(vb_hits["y"])**2)

    divided_hits = {}

    vb_layers = np.array(det_params["vb"]["r"])

    # Add 0 at the start and inf at the end
    vb_layer_midpoints = np.concatenate(([0], (vb_layers[:-1] + vb_layers[1:]) / 2, [np.inf]))

    for i, midpoint in enumerate(vb_layer_midpoints):
        if i == 0:
            continue

        hit_indices = np.where((vb_hit_radii > vb_layer_midpoints[i-1]) & (vb_hit_radii < midpoint))[0]

        divided_hits[f"vb_{i}"] = {
            "x": vb_hits["x"][hit_indices],
            "y": vb_hits["y"][hit_indices],
            "z": vb_hits["z"][hit_indices],
            "t": vb_hits["t"][hit_indices],
        }

    if det_mod.split("_")[1] != "FCCee":
        return divided_hits

    ve_hits = {k: np.array(v) for k, v in hits["ve"].items()}

    ve_layers = np.array(det_params["ve"]["z"])
    ve_layer_midpoints = np.concatenate(([0], (ve_layers[:-1] + ve_layers[1:])/2, [np.inf]))

    ve_hit_z = np.array(ve_hits["z"])

    for i, midpoint in enumerate(ve_layer_midpoints):
        if i == 0:
            continue

        hit_indices = np.where((ve_hit_z > ve_layer_midpoints[i-1]) & (ve_hit_z < midpoint))[0]

        divided_hits[f"ve_{i}"] = {
            "x": ve_hits["x"][hit_indices],
            "y": ve_hits["y"][hit_indices],
            "z": ve_hits["z"][hit_indices],
            "t": ve_hits["t"][hit_indices],
        }

    return divided_hits