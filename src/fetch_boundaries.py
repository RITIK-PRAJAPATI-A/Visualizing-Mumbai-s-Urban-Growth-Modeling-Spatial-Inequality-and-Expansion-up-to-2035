"""
Mumbai Geographical Boundaries & AOI (Area of Interest) Handler
Fetches official Mumbai administrative wards (BMC 24 Wards) and defines the MMR extent.
"""

import os
import json
import urllib.request

# Mumbai Metropolitan Region (MMR) Bounding Box:
# Covers South Mumbai up to Virar (North), Kalyan/Dombivli/Badlapur (East), and Navi Mumbai/Panvel (South-East)
MMR_BBOX = {
    "west": 72.75,
    "south": 18.85,
    "east": 73.20,
    "north": 19.45
}

# Official Mumbai BMC 24 Admin Wards GeoJSON URL
MUMBAI_WARDS_URL = "https://raw.githubusercontent.com/sanjanakrishnan/mumbai_spatial_data/master/BMC_admin_wards.geojson"

def download_mumbai_wards(output_path: str = "data/raw/mumbai_bmc_wards.geojson") -> str:
    """Downloads Mumbai 24 Administrative Wards GeoJSON if not present."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(output_path):
        print(f"[*] Mumbai wards already exists at: {output_path}")
        return output_path
        
    print(f"[*] Downloading Mumbai municipal wards from open spatial repo...")
    try:
        req = urllib.request.Request(
            MUMBAI_WARDS_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(output_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"[SUCCESS] Downloaded Mumbai wards boundary to: {output_path}")
    except Exception as e:
        print(f"[!] Warning: Could not download from DataMeet direct link: {e}")
        # Fallback: Create GeoJSON bounding polygon for Mumbai region
        fallback_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"name": "Mumbai Metropolitan Region (MMR)"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [MMR_BBOX["west"], MMR_BBOX["south"]],
                        [MMR_BBOX["east"], MMR_BBOX["south"]],
                        [MMR_BBOX["east"], MMR_BBOX["north"]],
                        [MMR_BBOX["west"], MMR_BBOX["north"]],
                        [MMR_BBOX["west"], MMR_BBOX["south"]]
                    ]]
                }
            }]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fallback_geojson, f, indent=2)
        print(f"[*] Fallback MMR boundary box written to: {output_path}")

    return output_path

if __name__ == "__main__":
    download_mumbai_wards()
