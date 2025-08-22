import re
import xml.etree.ElementTree as ET

from numpy import pi

from det_mod_configs import sub_det_cols_fcc, sub_det_cols_ilc

xmlPath = "../k4geo/FCCee/CLD/compact/CLD_o2_v07/Vertex_o4_v07_smallBP.xml"
KEYWORDS = ["VertexEndcap_z", "VertexEndcap_rmax", "VertexBarrel_r", "VertexBarrel_zmax"]
# Cannot find values stored in xml file for ILC model. This should be changed for single source of truth
ILC_RADII = [16, 37, 58]  # mm
ILC_HALF_LENGTHS = [625, 1250, 1250]


def extract_value_in_mm(text):
    match = re.search(r"([-+]?\d*\.?\d+)\s*\*?\s*(cm|mm)", text.lower())
    if not match:
        raise ValueError(f"Invalid format: {text}")

    value, unit = match.groups()
    value = float(value)

    if unit == "cm":
        return value * 10  # Convert to mm
    elif unit == "mm":
        return value


def extract_constants(xml_path=xmlPath, keywords=KEYWORDS):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    constants = {}

    for const in root.findall(".//constant"):
        name = const.get("name")
        value = const.get("value")

        if name is None or value is None:
            continue

        # Check if the name matches one of the keywords
        for k in keywords:
            if name.startswith(k):
                if k not in constants:
                    constants[k] = []
                constants[k].append(extract_value_in_mm(value))

    return constants


def calculate_barrel_area(radii, half_lengths, sub_det_cols):
    if len(half_lengths) == 1:
        half_lengths *= len(radii)

    total_area = 0
    for i, r in enumerate(radii):
        total_area += 2 * pi * r * 2 * half_lengths[i]
    if not sub_det_cols["vb"].only_double_layers:
        return total_area
    for i, r in enumerate(radii):
        total_area += 2 * pi * (r + 2) * 2 * half_lengths[i]
    return total_area

def get_areas():
    constants = extract_constants()

    fcc_barrel_area = calculate_barrel_area(constants["VertexBarrel_r"], constants["VertexBarrel_zmax"], sub_det_cols_fcc)
    fcc_endcap_area = pi * constants["VertexEndcap_rmax"][0]**2 * len(constants["VertexEndcap_z"]) * 2

    ilc_barrel_area = calculate_barrel_area(ILC_RADII, ILC_HALF_LENGTHS, sub_det_cols_ilc)

    subdetector_areas = {
        "ILD_FCCee_v01": {
            "vb": fcc_barrel_area,
            "ve": fcc_endcap_area,
        },
        "ILD_FCCee_v02": {
            "vb": fcc_barrel_area,
            "ve": fcc_endcap_area,
        },
        "ILD_l5_v02": {
            "vb": ilc_barrel_area,
        },
    }
    return subdetector_areas
