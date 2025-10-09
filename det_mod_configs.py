"""
contains detector model data:
    1. path to the model's compact file
    2. path to correct ddsim file
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from g4units import rad

DEFAULT_DETECTOR_MODELS = "ILD_FCCee_v01", "ILD_l5_v02"


# Define the dataclass
@dataclass
class HitCollection:
    root_tree_branch_name: str
    plot_collection_prefix: str
    only_double_layers: bool


@dataclass
class AcceleratorConfig:
    name: str
    relative_compact_file_dir: Path
    sim_crossing_angle_boost: float


@dataclass
class DetectorConfig:
    accelerator: AcceleratorConfig
    relative_compact_file_path: str
    sub_detector_collections: Dict

    def get_compact_file_path(self) -> Path:
        # Combine the directory from the accelerator with the relative compact file path
        return (
            self.accelerator.relative_compact_file_dir / self.relative_compact_file_path
        )

    def get_crossing_angle(self) -> float:
        return self.accelerator.sim_crossing_angle_boost

    def is_accelerator_ilc(self) -> bool:
        return self.accelerator.name == "ILC"

    def is_accelerator_fccee(self) -> bool:
        return self.accelerator.name == "FCCee"

    def get_sub_detector_collection_info(self) -> Dict:
        return self.sub_detector_collections


FCC_crossing_angle_boost = 15.0e-3
ILC_crossing_angle_boost = 7.0e-3
ild4FCC_dir = Path("FCCee") / "ILD_FCCee" / "compact"
ild4ILC_dir = Path("ILD") / "compact" / "ILD_sl5_v02"


accelerators = {
    "FCCee": AcceleratorConfig("FCCee", ild4FCC_dir, 15.0e-3 * rad),
    "ILC": AcceleratorConfig("ILC", ild4ILC_dir, 7.0e-3 * rad),
}


sub_det_cols_fcc = {
    "vb": HitCollection(
        root_tree_branch_name="VertexBarrelCollection",
        plot_collection_prefix="Vertex Barrel",
        only_double_layers=True,
    ),
    "ve": HitCollection(
        root_tree_branch_name="VertexEndcapCollection",
        plot_collection_prefix="Vertex Endcap",
        only_double_layers=True,
    ),
    "tpc": HitCollection(
        root_tree_branch_name="TPCLowPtCollection",
        plot_collection_prefix="Time Projection Chamber",
        only_double_layers=False,
    ),
}

sub_det_cols_ilc = {
    "vb": HitCollection(
        root_tree_branch_name="VXDCollection",
        plot_collection_prefix="Vertex",
        only_double_layers=True,
    ),
    "f": HitCollection(
        root_tree_branch_name="FTDCollection",
        plot_collection_prefix="Forward",
        only_double_layers=True,
    ),
    "tpc": HitCollection(
        root_tree_branch_name="TPCLowPtCollection",
        plot_collection_prefix="Time Projection Chamber",
        only_double_layers=False,
    ),
}


detector_model_configurations = {
    "ILD_FCCee_v01": DetectorConfig(
        accelerators["FCCee"],
        "ILD_FCCee_v01/ILD_FCCee_v01.xml",
        sub_det_cols_fcc,
    ),
    "ILD_FCCee_v01_fields": DetectorConfig(
        accelerators["FCCee"],
        "ILD_FCCee_v01_fields/ILD_FCCee_v01_fields.xml",
        sub_det_cols_fcc,
    ),
    "ILD_FCCee_v01_fields_noMask": DetectorConfig(
        accelerators["FCCee"],
        "ILD_FCCee_v01_fields_noMask/ILD_FCCee_v01_fields_noMask.xml",
        sub_det_cols_fcc,
    ),
    "ILD_FCCee_v02": DetectorConfig(
        accelerators["FCCee"],
        "ILD_FCCee_v02/ILD_FCCee_v02.xml",
        sub_det_cols_fcc,
    ),
    "ILD_l5_v02": DetectorConfig(
        accelerators["ILC"],
        "ILD_l5_v02.xml",
        sub_det_cols_ilc,
    ),  # uniform solenoid field
    "ILD_l5_v03": DetectorConfig(
        accelerators["ILC"],
        "ILD_l5_v03.xml",
        sub_det_cols_ilc,
    ),  # realistic solenoid field
    "ILD_l5_v05": DetectorConfig(
        accelerators["ILC"],
        "ILD_l5_v05.xml",
        sub_det_cols_ilc,
    ),  # realistic solenoid field & anti-DID field
}

CHOICES_DETECTOR_MODELS = tuple(detector_model_configurations.keys())


def get_paths_and_detector_configs():
    return detector_model_configurations
