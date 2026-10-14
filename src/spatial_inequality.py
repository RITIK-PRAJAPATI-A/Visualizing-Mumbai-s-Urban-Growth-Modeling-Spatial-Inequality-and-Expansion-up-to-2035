"""
Spatial Inequality Analyzer for Mumbai (BMC 24 Administrative Wards)
Pulls Earth Engine Zonal Statistics for:
1. GHSL Built-Up Density across epochs (2000, 2010, 2015, 2020)
2. Sentinel-2 NDVI (Vegetation disparity / Green access)
3. Sentinel-2 NDBI (Built-up index / Impervious heat traps)
4. VIIRS Nighttime Lights (Economic activity proxy)
5. WorldPop Gridded Population (Density per ward)
"""

import os
import json
import ee

PROJECT_ID = os.environ.get("GEE_PROJECT", "your-gee-project-id")
WARDS_GEOJSON_PATH = "data/raw/mumbai_bmc_wards.geojson"
OUTPUT_METRICS_PATH = "data/processed/mumbai_ward_inequality.json"

def initialize_gee(project_id: str = PROJECT_ID):
    try:
        ee.Initialize(project=project_id)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project_id)

def load_wards_fc() -> ee.FeatureCollection:
    """Loads Mumbai 24 BMC wards GeoJSON into an Earth Engine FeatureCollection."""
    with open(WARDS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    
    features = []
    for feat in geojson["features"]:
        geom = feat["geometry"]
        props = feat["properties"]
        ee_geom = ee.Geometry(geom)
        features.append(ee.Feature(ee_geom, props))
        
    return ee.FeatureCollection(features)

def compute_ward_metrics():
    """Computes Earth Engine zonal statistics for all 24 wards."""
    print("[*] Initializing Earth Engine...")
    initialize_gee()
    
    print("[*] Loading Mumbai 24 Administrative Wards...")
    wards_fc = load_wards_fc()
    
    # Define datasets
    print("[*] Preparing satellite imagery layers...")
    # 1. GHSL Built-up Surface (2000, 2010, 2020 for growth baseline)
    ghsl_2000 = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2000").select("built_surface").rename("built_2000")
    ghsl_2010 = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2010").select("built_surface").rename("built_2010")
    ghsl_2020 = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020").select("built_surface").rename("built_2020")
    
    # 2. Sentinel-2 Pre-monsoon composite (Jan-Apr 2023)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(wards_fc.geometry())
        .filterDate("2023-01-01", "2023-04-30")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
        .median()
    )
    ndvi = s2.normalizedDifference(["B8", "B4"]).rename("ndvi_greenery")
    ndbi = s2.normalizedDifference(["B11", "B8"]).rename("ndbi_built")
    
    # 3. VIIRS Nighttime Lights (2022 Annual Composite)
    viirs = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate("2022-01-01", "2022-12-31")
        .select("avg_rad")
        .median()
        .rename("night_lights")
    )
    
    # 4. WorldPop (Population per pixel)
    pop = (
        ee.ImageCollection("WorldPop/GP/100m/pop")
        .filter(ee.Filter.eq("country", "IND"))
        .filter(ee.Filter.calendarRange(2020, 2020, "year"))
        .first()
        .select("population")
        .rename("population_density")
    )
    
    # Combine all layers into a single multiband image
    composite = ghsl_2000.addBands([
        ghsl_2010,
        ghsl_2020,
        ndvi,
        ndbi,
        viirs,
        pop
    ])
    
    print("[*] Computing zonal statistics across all 24 wards in Earth Engine Cloud...")
    reduced = composite.reduceRegions(
        collection=wards_fc,
        reducer=ee.Reducer.mean(),
        scale=100
    )
    
    features_info = reduced.getInfo()["features"]
    
    ward_results = []
    for f in features_info:
        props = f["properties"]
        ward_name = props.get("name", "Unknown")
        
        b2000 = props.get("built_2000", 0) or 0
        b2010 = props.get("built_2010", 0) or 0
        b2020 = props.get("built_2020", 0) or 0
        green = props.get("ndvi_greenery", 0) or 0
        built_idx = props.get("ndbi_built", 0) or 0
        ntl = props.get("night_lights", 0) or 0
        pop_dens = props.get("population_density", 0) or 0
        
        # Calculate 20-year built-up expansion rate (%)
        growth_rate = ((b2020 - b2000) / (b2000 + 1e-5)) * 100 if b2000 > 0 else 0
        
        # Economic intensity per capita proxy (NTL / population density)
        econ_per_capita = (ntl / (pop_dens + 1.0)) * 1000
        
        ward_results.append({
            "ward": ward_name,
            "built_up_2000": round(float(b2000), 2),
            "built_up_2010": round(float(b2010), 2),
            "built_up_2020": round(float(b2020), 2),
            "growth_rate_pct": round(float(growth_rate), 2),
            "ndvi_greenery": round(float(green), 4),
            "ndbi_built_index": round(float(built_idx), 4),
            "nighttime_lights": round(float(ntl), 2),
            "population_density": round(float(pop_dens), 1),
            "economic_intensity_proxy": round(float(econ_per_capita), 2)
        })
        
    os.makedirs(os.path.dirname(OUTPUT_METRICS_PATH), exist_ok=True)
    with open(OUTPUT_METRICS_PATH, "w", encoding="utf-8") as out:
        json.dump(ward_results, out, indent=2)
        
    print(f"\n[SUCCESS] Successfully computed zonal inequality metrics for {len(ward_results)} wards!")
    print(f"[*] Saved to: {OUTPUT_METRICS_PATH}")
    
    # Display top 5 and bottom 5 by green space & economic intensity
    sorted_by_green = sorted(ward_results, key=lambda x: x["ndvi_greenery"], reverse=True)
    print("\n--- TOP 3 WARDS BY GREEN COVER (NDVI) ---")
    for w in sorted_by_green[:3]:
        print(f"  Ward {w['ward']}: NDVI = {w['ndvi_greenery']} (High Tree Canopy/Open Areas)")
        
    print("\n--- BOTTOM 3 WARDS BY GREEN COVER (NDVI) ---")
    for w in sorted_by_green[-3:]:
        print(f"  Ward {w['ward']}: NDVI = {w['ndvi_greenery']} (Severe Green Deficit/High Density)")

    sorted_by_ntl = sorted(ward_results, key=lambda x: x["nighttime_lights"], reverse=True)
    print("\n--- TOP 3 WARDS BY NIGHTTIME LIGHT RADIANCE (ECONOMIC ACTIVITY) ---")
    for w in sorted_by_ntl[:3]:
        print(f"  Ward {w['ward']}: NTL = {w['nighttime_lights']} nW/cm²/sr")

    print("\n--- BOTTOM 3 WARDS BY NIGHTTIME LIGHT RADIANCE ---")
    for w in sorted_by_ntl[-3:]:
        print(f"  Ward {w['ward']}: NTL = {w['nighttime_lights']} nW/cm²/sr")

    return ward_results

if __name__ == "__main__":
    compute_ward_metrics()
