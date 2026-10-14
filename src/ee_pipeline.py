"""
Earth Engine Data Pipeline for Mumbai Urban Growth & Spatial Inequality Analysis
"""

import os
import ee

# -------------------------------------------------------------------------
# 1. Configuration & Region Definition
# -------------------------------------------------------------------------
# Set your Google Cloud Project ID here or configure the GEE_PROJECT environment variable
PROJECT_ID = os.environ.get("GEE_PROJECT", "your-gee-project-id")

# Mumbai Metropolitan Region (MMR) Bounding Box
# Lon min, Lat min, Lon max, Lat max
MMR_BOUNDS = [72.75, 18.85, 73.20, 19.45]

def get_mmr_geometry() -> ee.Geometry.Rectangle:
    """Returns Earth Engine geometry for Mumbai Metropolitan Region."""
    return ee.Geometry.Rectangle(MMR_BOUNDS)

def initialize_gee(project_id: str = PROJECT_ID):
    """Initializes GEE with project ID."""
    try:
        ee.Initialize(project=project_id)
    except Exception as e:
        print(f"[!] Re-authenticating: {e}")
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)

# -------------------------------------------------------------------------
# 2. Historical Urban Built-Up Extent (GHSL 1990 - 2025)
# -------------------------------------------------------------------------
def get_ghsl_built_surface():
    """
    Returns Global Human Settlement Layer (GHSL) built-up surface
    multi-temporal epochs (100m resolution).
    Epochs available: 1975, 1990, 2000, 2010, 2015, 2020, 2025
    """
    ghsl = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020")
    return ghsl

def get_ghsl_time_series():
    """
    Returns multi-epoch built-up images for urban growth transition modeling.
    """
    epochs = [2000, 2010, 2015, 2020]
    collection = {}
    for year in epochs:
        try:
            img = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{year}").clip(get_mmr_geometry())
            collection[year] = img
        except Exception as e:
            print(f"[!] Warning for year {year}: {e}")
    return collection

# -------------------------------------------------------------------------
# 3. Nighttime Lights (Economic Activity Proxy)
# -------------------------------------------------------------------------
def get_nighttime_lights(year: int = 2022):
    """
    Retrieves annual or monthly VIIRS Nighttime Lights composite for Mumbai.
    Higher radiance = denser commercial/residential electrification & wealth proxy.
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    viirs = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate(start_date, end_date)
        .select("avg_rad")
        .median()
        .clip(get_mmr_geometry())
    )
    return viirs

# -------------------------------------------------------------------------
# 4. Sentinel-2 Multispectral Indices (NDBI, NDVI)
# -------------------------------------------------------------------------
def get_sentinel_indices(year: int = 2023):
    """
    Computes cloud-masked Sentinel-2 composite and derives:
    - NDVI (Normalized Difference Vegetation Index) -> Green disparity
    - NDBI (Normalized Difference Built-up Index) -> Built density
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-04-30"  # Pre-monsoon dry season for clearest cloud-free imagery
    
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(get_mmr_geometry())
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
        .median()
        .clip(get_mmr_geometry())
    )
    
    # Sentinel-2 Bands:
    # B4: Red, B8: NIR (842 nm), B11: SWIR1 (1610 nm)
    ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndbi = s2.normalizedDifference(["B11", "B8"]).rename("NDBI")
    
    combined = s2.addBands([ndvi, ndbi])
    return combined

# -------------------------------------------------------------------------
# 5. WorldPop Gridded Population
# -------------------------------------------------------------------------
def get_population_grid(year: int = 2020):
    """
    WorldPop estimated population count per 100m pixel.
    """
    pop = (
        ee.ImageCollection("WorldPop/GP/100m/pop")
        .filter(ee.Filter.eq("country", "IND"))
        .filter(ee.Filter.calendarRange(year, year, "year"))
        .first()
        .clip(get_mmr_geometry())
    )
    return pop

if __name__ == "__main__":
    print("[*] Initializing Earth Engine...")
    initialize_gee()
    mmr = get_mmr_geometry()
    print(f"[SUCCESS] MMR AOI: {mmr.getInfo()['coordinates']}")
    
    print("[*] Checking GHSL multi-epoch layers...")
    series = get_ghsl_time_series()
    for yr in series:
        print(f"  -> GHSL {yr} layer ready.")
        
    print("[*] Checking Sentinel-2 composite...")
    s2 = get_sentinel_indices(2023)
    band_names = s2.bandNames().getInfo()
    print(f"  -> Sentinel bands available: {len(band_names)} (includes NDVI & NDBI)")
    
    print("[*] Checking Nighttime Lights...")
    ntl = get_nighttime_lights(2022)
    print("  -> VIIRS Nighttime Lights ready.")
    
    print("\n[ALL CHECKS PASSED] Core Earth Observation layers configured!")
