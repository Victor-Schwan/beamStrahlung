import re
import xml.etree.ElementTree as ET
from numpy import pi
from det_mod_configs import sub_det_cols_fcc, sub_det_cols_ilc

vertex_xml = "../k4geo/FCCee/CLD/compact/CLD_o2_v07/Vertex_o4_v07_smallBP.xml"
large_TPC_xml = "../k4geo/FCCee/ILD_FCCee/compact/ILD_FCCee_v01/top_defs_ILD_FCCee_v01.xml"
small_TPC_xml = "../k4geo/FCCee/ILD_FCCee/compact/ILD_FCCee_v02/top_defs_ILD_FCCee_v02.xml"
TPC_pixel_xml = "../k4geo/FCCee/ILD_FCCee/compact/ILD_common_v02/tpc10_01.xml"

# vertex_pixel_size taken from 'CLD - A Detector Concept for the FCC-ee'. Could not locate in k4Geo (potential violation of single source of truth)
vertex_pixel_size = 0.025 # mm

KEYWORDS = {
    "Vertex": ["VertexEndcap_z", "VertexEndcap_rmax", "VertexBarrel_r", "VertexBarrel_zmax"],
    "TPC": ["top_TPC_inner_radius", "top_TPC_outer_radius"],
}
# Cannot find values stored in xml file for ILC model. This should be changed for single source of truth
ILC_vb_params = {
    "r": [16, 37, 58], # radii mm
    "z": [62.5, 125, 125], # half lengths mm
    "a": [],
}

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
    
def get_tpc_pixel_size(xml_path=TPC_pixel_xml):
    tree = ET.parse(xml_path) 
    root = tree.getroot()

    # Find the <global> element inside the TPC detector
    for detector in root.findall(".//detector"):
        if detector.get("name") == "TPC":
            global_elem = detector.find("global")
            if global_elem is not None:
                pad_height_str = global_elem.get("TPC_pad_height")
                pad_width_str  = global_elem.get("TPC_pad_width")

                # strip "*mm" and convert to float
                pad_height = float(pad_height_str.replace("*mm", ""))
                pad_width  = float(pad_width_str.replace("*mm", ""))

                area_mm2 = pad_height * pad_width
                return area_mm2
            
pixel_areas = {
    "TPC": get_tpc_pixel_size(),
    "Vertex": vertex_pixel_size**2,
}

def split_double_layers(parameters):

    for det_mod, det_params in parameters.items():
        if SUB_DET_COLS[det_mod]["vb"].only_double_layers:
            parameters[det_mod]["Vertex"]["vb"]["r"] = [radius for r in det_params["Vertex"]["vb"]["r"] for radius in (r, r + 2)]
            parameters[det_mod]["Vertex"]["vb"]["z"] = [half_length for z in det_params["Vertex"]["vb"]["z"] for half_length in (z, z)]
        if det_mod.split("_")[1] != "FCCee":
            continue
        if SUB_DET_COLS[det_mod]["ve"].only_double_layers:
            parameters[det_mod]["Vertex"]["ve"]["r"] = [radius for r in det_params["Vertex"]["ve"]["r"] for radius in (r, r)]
            parameters[det_mod]["Vertex"]["ve"]["z"] = [pos for z in det_params["Vertex"]["ve"]["z"] for pos in (z, z + 2)]

    return parameters

def extract_constants(xml_path, keywords):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    subdet_params = {}

    for const in root.findall(".//constant"):
        name = const.get("name")
        value = const.get("value")

        if name is None or value is None:
            continue

        # Check if the name matches one of the keywords
        for k in keywords:
            if name.startswith(k):
                if k not in subdet_params:
                    subdet_params[k] = []
                subdet_params[k].append(extract_value_in_mm(value))
    
    return subdet_params

def calculate_barrel_area(subdet_params, sub_det_cols, layer):

    radius = subdet_params["vb"]["r"][layer]
    half_length = subdet_params["vb"]["z"][layer]

    area = 2 * pi * radius * 2 * half_length
    if not sub_det_cols["vb"].only_double_layers:
        return area
    area += 2 * pi * (radius + 2) * 2 * half_length
    return area

def calculate_endcap_area(subdet_params, sub_det_cols, layer):
    radius = subdet_params["ve"]["r"][layer]
    
    # factor of 2 to include both endcaps
    area = 2 * pi * radius**2 
    return area

def calculate_TPC_area(tpc_params):
    return 2 * pi * (tpc_params["r_outer"][0]**2 - tpc_params["r_inner"][0]**2)

def get_area(parameters):

    parameters = split_double_layers(parameters)

    new_params = {}
    for det_mod, det_params in parameters.items():
        # --- Vertex ---
        vb_areas = [
            calculate_barrel_area(det_params["Vertex"], SUB_DET_COLS[det_mod], i)
            for i in range(len(det_params["Vertex"]["vb"]["r"]))
        ]
        ve_areas = [
            calculate_endcap_area(det_params["Vertex"], SUB_DET_COLS[det_mod], i)
            for i in range(len(det_params["Vertex"]["ve"]["z"]))
        ]
        vb_pixels = [a / pixel_areas["Vertex"] for a in vb_areas]
        ve_pixels = [a / pixel_areas["Vertex"] for a in ve_areas]

        # --- TPC ---
        tpc_area = calculate_TPC_area(det_params["TPC"]["TPC"])
        tpc_pixels = tpc_area / pixel_areas["TPC"]

        # --- Assemble ---
        new_params[det_mod] = {
            **det_params,
            "Vertex": {
                **det_params["Vertex"],
                "vb": {**det_params["Vertex"]["vb"], "a": vb_areas, "n_pixels": vb_pixels},
                "ve": {**det_params["Vertex"]["ve"], "a": ve_areas, "n_pixels": ve_pixels},
            },
            "TPC": {
                **det_params["TPC"],
                "TPC": {**det_params["TPC"]["TPC"], "a": [tpc_area], "n_pixels": [tpc_pixels]},
            },
        }

    return new_params

def get_params():

    fcc_vertex_params = extract_constants(vertex_xml, KEYWORDS["Vertex"])
    large_TPC_params = extract_constants(large_TPC_xml, KEYWORDS["TPC"])
    small_TPC_params = extract_constants(small_TPC_xml, KEYWORDS["TPC"])

    parameters = {
        "ILD_FCCee_v01": {
            "Vertex": {
                "vb": {
                    "r": fcc_vertex_params["VertexBarrel_r"],
                    "z": fcc_vertex_params["VertexBarrel_zmax"] * len(fcc_vertex_params["VertexBarrel_r"]),
                    "a": [],
                    "n_pixels": [],
                },
                "ve": {
                    "r": fcc_vertex_params["VertexEndcap_rmax"] * len(fcc_vertex_params["VertexEndcap_z"]),
                    "z": fcc_vertex_params["VertexEndcap_z"],
                    "a": [],
                    "n_pixels": [],
                }
            },
            "TPC": {
                "TPC": {
                    "r_inner": large_TPC_params["top_TPC_inner_radius"],
                    "r_outer": large_TPC_params["top_TPC_outer_radius"],
                    "z": [],
                    "a": [],
                    "n_pixels": [],
                }
            },
        },
        "ILD_FCCee_v02": {
            "Vertex": {
                "vb": {
                    "r": fcc_vertex_params["VertexBarrel_r"],
                    "z": fcc_vertex_params["VertexBarrel_zmax"] * len(fcc_vertex_params["VertexBarrel_r"]),
                    "a": [],
                    "n_pixels": [],
                },
                "ve": {
                    "r": fcc_vertex_params["VertexEndcap_rmax"] * len(fcc_vertex_params["VertexEndcap_z"]),
                    "z": fcc_vertex_params["VertexEndcap_z"],
                    "a": [],
                    "n_pixels": [],
                }
            },
            "TPC": {
                "TPC": {
                    "r_inner": small_TPC_params["top_TPC_inner_radius"],
                    "r_outer": small_TPC_params["top_TPC_outer_radius"],
                    "z": [],
                    "a": [],
                    "n_pixels": [],
                }
            },
        },
        "ILD_l5_v02": {
            "Vertex": {
                "vb": {
                    "r": ILC_vb_params["r"],
                    "z": ILC_vb_params["z"],
                    "a": [],
                    "n_pixels": [],
                },
                "ve": {
                    "r": [],
                    "z": [],
                    "a": [],
                    "n_pixels": [],
                },
            },
            "TPC": {
                "TPC": {
                    "r_inner": large_TPC_params["top_TPC_inner_radius"],
                    "r_outer": large_TPC_params["top_TPC_outer_radius"],
                    "z": [],
                    "a": [],
                    "n_pixels": [],
                }
            },
        },
    }

    return get_area(parameters)