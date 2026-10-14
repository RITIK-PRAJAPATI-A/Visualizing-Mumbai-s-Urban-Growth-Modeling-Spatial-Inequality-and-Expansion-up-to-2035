"""
Script to verify Google Earth Engine connection and test project access.
Project ID: maximal-dynamo-506718-g8
"""

import sys

def test_connection(project_id: str = "maximal-dynamo-506718-g8"):
    try:
        import ee
    except ImportError:
        print("[ERROR] earthengine-api is not installed.")
        sys.exit(1)

    print(f"[*] Attempting to initialize Earth Engine with project: {project_id}...")
    try:
        ee.Initialize(project=project_id)
        print("[SUCCESS] Earth Engine initialized successfully!")
    except Exception as e:
        print(f"[!] Initialization failed: {e}")
        print("[*] Running authentication flow...")
        try:
            ee.Authenticate()
            ee.Initialize(project=project_id)
            print("[SUCCESS] Earth Engine authenticated and initialized successfully!")
        except Exception as auth_err:
            print(f"[ERROR] Authentication failed: {auth_err}")
            sys.exit(1)

    # Test query on Mumbai coordinates
    try:
        mumbai_point = ee.Geometry.Point([72.8777, 19.0760])
        elevation_image = ee.Image("USGS/SRTMGL1_003")
        elevation = elevation_image.sample(mumbai_point, 30).first().get("elevation").getInfo()
        print(f"[SUCCESS] Test query passed: Mumbai elevation at center point = {elevation}m")
    except Exception as query_err:
        print(f"[!] Warning during test query: {query_err}")

if __name__ == "__main__":
    PROJECT_ID = "maximal-dynamo-506718-g8"
    test_connection(PROJECT_ID)
