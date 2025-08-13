import re
import xml.etree.ElementTree as ET
from numpy import pi

xmlPath = "../k4geo/FCCee/CLD/compact/CLD_o2_v07/Vertex_o4_v07_smallBP.xml"

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

def extract_constants(xml_path, keywords):
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

def get_areas():

    keywords = ["VertexEndcap_z", "VertexEndcap_rmax", "VertexBarrel_r", "VertexBarrel_zmax"]
    constants = extract_constants(xmlPath, keywords)

    total_barrel_area = 0
    for r in constants["VertexBarrel_r"]:
        total_barrel_area += 2 * pi * r * constants["VertexBarrel_zmax"][0] * 2

    total_endcap_area = pi * constants["VertexEndcap_rmax"][0]**2 * len(constants["VertexEndcap_z"])

    return total_barrel_area, total_endcap_area
    