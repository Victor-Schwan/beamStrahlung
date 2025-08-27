import re
import xml.etree.ElementTree as ET

from numpy import pi

from det_mod_configs import sub_det_cols_fcc, sub_det_cols_ilc

xmlPath = "../k4geo/FCCee/CLD/compact/CLD_o2_v07/Vertex_o4_v07_smallBP.xml"
KEYWORDS = ["VertexEndcap_z", "VertexEndcap_rmax", "VertexBarrel_r", "VertexBarrel_zmax"]
# Cannot find values stored in xml file for ILC model. This should be changed for single source of truth
ILC_RADII = [16, 37, 58] # mm
ILC_HALF_LENGTHS = [62.5, 125, 125]

SUB_DET_COLS = {
    "ILD_FCCee_v01": sub_det_cols_fcc,
    "ILD_FCCee_v02": sub_det_cols_fcc,
    "ILD_l5_v02": sub_det_cols_ilc,
}

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

    fcc_params = {}

    for const in root.findall(".//constant"):
        name = const.get("name")
        value = const.get("value")

        if name is None or value is None:
            continue

        # Check if the name matches one of the keywords
        for k in keywords:
            if name.startswith(k):
                if k not in fcc_params:
                    fcc_params[k] = []
                fcc_params[k].append(extract_value_in_mm(value))
        
    parameters = {
        "ILD_FCCee_v01": {
            "vb": {
                "r": fcc_params["VertexBarrel_r"],
                "z": fcc_params["VertexBarrel_zmax"] * len(fcc_params["VertexBarrel_r"]),
                "a": [],
            }, 
            "ve": {
                "r": fcc_params["VertexEndcap_rmax"] * len(fcc_params["VertexEndcap_z"]),
                "z": fcc_params["VertexEndcap_z"],
        },
        "ILD_FCCee_v02": {
            "vb": {
                "r": fcc_params["VertexBarrel_r"],
                "z": fcc_params["VertexBarrel_zmax"] * len(fcc_params["VertexBarrel_r"]),
                "a": [],
            }, 
            "ve": {
                "r": fcc_params["VertexEndcap_rmax"] * len(fcc_params["VertexEndcap_z"]),
                "z": fcc_params["VertexEndcap_z"],
                "a": [],
            }
        },
        "ILD_l5_v02": {
            "vb": {
                "r": ILC_RADII,
                "z": ILC_HALF_LENGTHS,
                "a": [],
            },
            "ve": {
                "r": [],
                "z": [],
                "a": [],
            }
        }
    }

    return parameters

def calculate_barrel_area(det_params, sub_det_cols, layer):

    radius = det_params["vb"]["r"][layer]
    half_length = det_params["vb"]["z"][layer]

    area = 2 * pi * radius * 2 * half_length
    if not sub_det_cols["vb"].only_double_layers:
        return area
    area += 2 * pi * (radius + 2) * 2 * half_length
    return area

def calculate_endcap_area(det_params, sub_det_cols, layer):
    radius = det_params["vb"]["r"][layer]
    
    # factor of 2 to include both endcaps
    area = 2 * pi * radius**2 
    if sub_det_cols["ve"].only_double_layers:
        area *= 2
    return area

def get_params():

    parameters = extract_constants()

    parameters = {
        det_mod: {
            **det_params,
            "vb": {
                **det_params["vb"],
                "a": [
                    calculate_barrel_area(det_params, SUB_DET_COLS[det_mod], i)
                    for i in range(len(det_params["vb"]["r"]))
                ],
            },
            "ve": {
                **det_params["ve"],
                "a": [
                    calculate_endcap_area(det_params, SUB_DET_COLS[det_mod], i)
                    for i in range(len(det_params["ve"]["z"]))
                ],
            },
        }
        for det_mod, det_params in parameters.items()
    }

