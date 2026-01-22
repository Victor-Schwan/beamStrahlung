"""
This module provides functionality to identify the current system based on the
username of the user executing the script. It utilizes a JSON configuration file to map
usernames to system name.
And further path utilities.
"""

import json
from enum import Enum
from os import environ
from pathlib import Path
from sys import version, version_info
from typing import Dict

edm4hep_file_suffix = ".edm4hep.root"

file_extensions = {
    "beamstrahlung": ".pairs",
    "synchrotron": ".hepevt",
}

# type hints with | require at least python 3.10
if version_info < (3, 10):
    raise RuntimeError(
        "Python 3.10 or later is required. You are using Python " + version
    )


class BGSourceKey(str, Enum):
    """Background source keys."""

    BS = "BS"  # beamstrahlung
    SR = "SR"  # synchrotron_radiation
    IN = "IN"  # injection


class AccSetupKey(str, Enum):
    """Accelerator setup keys."""

    ILC250 = "ILC250"  # ILC 250GeV
    FCC091 = "FCC091"  # FCCee 91GeV
    FCC240 = "FCC240"  # FCCee 240GeV


class MachineID(str, Enum):
    """Machine identifier constants."""

    KEK = "kek"
    DESY_NAF = "desy-naf"
    SPECTRE = "spectre"


# TODO: remove references to below, deprecated non-enum machine IDs
KEK_MACHINE_IDENTIFIER = MachineID.KEK
DESY_NAF_MACHINE_IDENTIFIER = MachineID.DESY_NAF
SPECTRE_MACHINE_IDENTIFIER = MachineID.SPECTRE

SIM_DATA_SUBDIR_NAME = "sim"
MY_CODE_DIR_ENV_VAR_NAME = "codeDir"


def get_path_from_env(env_var: str) -> Path:
    """
    Returns the value of an environment variable as a Path.

    Raises:
        EnvironmentError: If the environment variable is not set.
    """
    try:
        return Path(environ[env_var])
    except KeyError as e:
        raise EnvironmentError(f"Environment variable '{env_var}' is not set.") from e


code_dir = get_path_from_env(MY_CODE_DIR_ENV_VAR_NAME)
config_file_path = code_dir / "beamStrahlung" / "uname_to_sys_map.json"


class UnknownSystemError(Exception):
    """Custom exception raised when the system cannot be identified."""


def load_user_to_system_mapping(filepath: Path | str) -> dict:
    """
    Loads the user-to-system mapping from a JSON configuration file.

    Args:
        filepath (Path | str): The path to the JSON configuration file.

    Returns:
        dict: A dictionary mapping usernames to system names.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def identify_system() -> str:
    """
    Identifies the current system based on the username from environment variables
    and a configuration file mapping.

    Args:
        config_filepath (str): The path to the JSON configuration file.

    Returns:
        str: The name of the system associated with the current username.

    Raises:
        UnknownSystemError: If the username is not recognized or the 'USER' environment
        variable is not set.
        FileNotFoundError: If the specified configuration file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    user_to_system = load_user_to_system_mapping(config_file_path)

    current_user = environ["USER"]

    if current_user is None:
        raise UnknownSystemError("The USER environment variable is not set.")

    if current_user not in user_to_system:
        raise UnknownSystemError(f"Unknown system for user: {current_user}")

    return user_to_system[current_user]


SR_dir = Path("backgrounds/SR_FCCee/SR_v5_complete_giulia/")
SR_raw_input_dir = get_path_from_env("dtDir") / SR_dir / "raw_files"
SR_split_input_dir = get_path_from_env("dtDir") / SR_dir / "split_files"


def construct_SR_paths() -> Dict[str, Dict[MachineID, Path]]:
    """
    Returns:
    Dict[str, Dict[str, Path]]: The first key is the background scenario
                    and the second key is machine_identifier. The value
                    is the path of the data file on the chosen machine.
    """

    sr_data_paths = {
        "182GeV_nzco_10urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_5Mpositron_182GeVcom_nzco_10urad_v23_mediumfilter"
            ),
        },
        "182GeV_nzco_6urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_5Mpositron_182GeVcom_nzco_6urad_v23_mediumfilter"
            ),
        },
        "182GeV_nzco_2urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_5Mpositron_182GeVcom_nzco_2urad_v23_mediumfilter"
            ),
        },
        "182GeV_halo": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_80Mpositron_182GeVcom_halo_v23_mediumfilter"
            ),
        },
        "45GeV_halo": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_20Mpositron_45GeVcom_halo_v23_mediumfilter"
            ),
        },
        "45GeV_nzco_10urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_10Mpositron_45GeVcom_nzco_10urad_v23_mediumfilter"
            ),
        },
        "45GeV_nzco_6urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_10Mpositron_45GeVcom_nzco_6urad_v23_mediumfilter"
            ),
        },
        "45GeV_nzco_2urad": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                SR_split_input_dir
                / "sr_photons_from_10Mpositron_45GeVcom_nzco_2urad_v23_mediumfilter"
            ),
        },
    }

    return sr_data_paths


def construct_beamstrahlung_paths() -> Dict[str, Dict[str, Dict[str, Path]]]:
    """
    Construct a nested dictionary containing paths to beamstrahlung background files.

    The dictionary is structured as:
        background_paths[source][accelerator][machine] -> Path to data file

    Returns:
        Dict[str, Dict[str, Dict[str, Path]]]: A three-level nested dictionary with:
            - First key: background source (e.g. "BS")
            - Second key: accelerator setup (e.g. "ILC250")
            - Third key: machine identifier (e.g. "kek", "desy-naf")
            - Value: Path to the corresponding simulation data file
    """

    desy_dust_beamstrahlung_base_path = (
        get_path_from_env("dtDir") / "split_up_beamstrahlung_files"
    )

    beam_strahlung_data_paths = {
        "ILC250": {
            KEK_MACHINE_IDENTIFIER: Path(
                "/group/ilc/users/jeans/pairs-ILC250_gt2MeV/E250-SetA.PBeamstr-pairs.GGuineaPig-v1-4-4-gt2MeV.I270000.#N.pairs"
            ),
            DESY_NAF_MACHINE_IDENTIFIER: (
                desy_dust_beamstrahlung_base_path / "pairs-ILC250_gt2MeV/ILC250_#N"
                if desy_dust_beamstrahlung_base_path
                else ""
            ),
        },
        "FCC091": {
            DESY_NAF_MACHINE_IDENTIFIER: (
                desy_dust_beamstrahlung_base_path
                / "tpc-ion_tpc-bspairs_input-allatip/FCC091_#N"
                if desy_dust_beamstrahlung_base_path
                else ""
            ),
        },
        "FCC240": {
            KEK_MACHINE_IDENTIFIER: Path(
                "/home/ilc/jeans/guineaPig/fromAndrea/pairs100/allAtIP_ZH/FCC240_#N"
            ),
            DESY_NAF_MACHINE_IDENTIFIER: (
                desy_dust_beamstrahlung_base_path
                / "guineaPig_fromAndrea_pairs100_allAtIP-ZH/FCC240_#N"
                if desy_dust_beamstrahlung_base_path
                else ""
            ),
        },
    }

    return beam_strahlung_data_paths


def flatten_bg_paths(nested: dict) -> dict[str, str]:
    """
    Convert the nested {scenario: {MachineID: Path}} structure
    into a flat {scenario: str} mapping that contains only the
    relative path component.
    """
    return {
        str(next(iter(machine_map.values())).name): scenario
        for scenario, machine_map in nested.items()
    }


def construct_paths(is_executed_on_desy_naf):
    bs_data_paths = construct_beamstrahlung_paths()

    if not is_executed_on_desy_naf:
        raise UnknownSystemError  # SR Paths only on NAF defined
    sr_data_paths = construct_SR_paths()

    return bs_data_paths, sr_data_paths


def get_path_for_current_machine(path_dict: dict) -> Path:
    """
    Retrieves the appropriate path based on the current machine's identifier.

    This function utilizes the `identify_system` function to determine the current
    machine's identifier and then retrieves the appropriate path from the given `path_dict`.

    Parameters:
    path_dict (dict): A dictionary with system identifiers as keys and `Path` objects as values.

    Returns:
    Path: The path corresponding to the current machine, as specified in `path_dict`.

    Raises:
    UnknownSystemError: If the system identifier returned by `identify_system()` does not
                         match any key in `path_dict`, indicating that the machine is
                         unknown or not configured.
    """
    system_key = identify_system()

    if system_key in path_dict:
        return path_dict[system_key]

    raise UnknownSystemError(
        f"Machine unknown. The system identifier '{system_key}' is not configured in the provided path dictionary."
    )


def resolve_path_with_env(input_path: str | Path, env_var_name: str) -> Path:
    """
    Returns an absolute Path object by combining a given path with a specified environment variable if necessary.

    This function checks whether the given path is absolute. If it is absolute, it returns the path as a Path object.
    If the path is not absolute, the function checks for the presence of the specified environment variable. If the
    environment variable is set, the function combines its value with the given relative path and returns the
    resulting absolute Path object. If the environment variable is not set, an EnvironmentError is raised.

    Parameters:
    - input_path (str or Path): The input path (string) to be processed.
    - env_var_name (str): The name of the environment variable to be used for constructing the absolute path if
      the input path is not absolute.

    Returns:
    - Path: An absolute Path object representing the combined path.

    Raises:
    - EnvironmentError: If the input path is not absolute and the specified environment variable is not set.
    """

    path = Path(input_path)

    # Check if the input path is already absolute
    if path.is_absolute():
        return path

    # Check if the specified environment variable is set
    env_var_value = get_path_from_env(env_var_name)

    # Combine the environment variable value with the provided path
    combined_path = Path(env_var_value) / path
    return combined_path
