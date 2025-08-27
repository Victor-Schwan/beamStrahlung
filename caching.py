import pickle
from pathlib import Path
from typing import List, Tuple

from analyze_bs import get_hits, get_p_n_t
from utils import split_pos_n_time


def get_cache_filename(cache_dir, detector_model, scenario, num_bX):
    """Generate a unique cache filename based on the detector model, scenario, and number of bXs."""
    return f"{cache_dir}/cache_{detector_model}_{scenario}_{num_bX}.pkl"


def load_from_cache(cache_file):
    """Load data from cache if it exists."""
    if cache_file.exists():
        with cache_file.open("rb") as f:
            return pickle.load(f)
    return None


def save_to_cache(cache_file, data):
    """Save data to cache."""
    with cache_file.open("wb") as f:
        pickle.dump(data, f)


def handle_cache_operations(
    cache_dir: str,
    detector_model: str,
    scenario: str,
    num_bX: int,
    file_paths: List[str],
    split_p_n_t: bool = False,
) -> Tuple:
    """
    Handles the loading of data from cache or computing and caching the data
    if it's not already cached.

    Parameters:
    - cache_dir (str): The directory where cache files are stored.
    - detector_model (str): The detector model identifier.
    - scenario (str): The scenario identifier.
    - num_bX (int): An integer representing number of something (e.g., positions).
    - file_paths (List[str]): List of file paths to process if cache is not available.

    Returns:
    - Tuple: A tuple containing the positions and time.
    """

    # ensure the cache directory exists
    cache_dir_path = Path(cache_dir)
    cache_dir_path.mkdir(parents=True, exist_ok=True)

    cache_file = Path(get_cache_filename(cache_dir, detector_model, scenario, num_bX))
    cached_data = load_from_cache(cache_file)

    if split_p_n_t:
        if cached_data is not None:
            pos, time = cached_data
            print(
                f"Loaded data for Detector Model='{detector_model}', Scenario='{scenario}' from cache."
            )
        else:
            # TODO split_pos_n_time only because of legacy reasons, remove
            pos, time = split_pos_n_time(get_p_n_t(file_paths, detector_model))
            save_to_cache(cache_file, (pos, time))
            print(
                f"Data loaded and cached for Detector Model='{detector_model}', Scenario='{scenario}'."
            )

        return pos, time

    if cached_data is not None:
        hits = cached_data
        print(
            f"Loaded data for Detector Model='{detector_model}', Scenario='{scenario}' from cache."
        )
    else:
        # TODO split_pos_n_time only because of legacy reasons, remove
        #pos, time = split_pos_n_time(get_p_n_t(file_paths, detector_model))
        #save_to_cache(cache_file, (pos, time))
        hits = get_hits(file_paths, detector_model)
        save_to_cache(cache_file, hits)
        print(
            f"Data loaded and cached for Detector Model='{detector_model}', Scenario='{scenario}'."
        )

    return hits
