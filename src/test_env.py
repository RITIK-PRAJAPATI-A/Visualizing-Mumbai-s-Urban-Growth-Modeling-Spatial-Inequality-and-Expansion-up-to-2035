import sys

print("Python version:", sys.version)

modules = ['ee', 'numpy', 'requests', 'json', 'shapely', 'pandas', 'geopandas', 'matplotlib', 'sklearn']

for mod in modules:
    try:
        __import__(mod)
        print(f"[OK] {mod}")
    except Exception as e:
        print(f"[FAIL] {mod}: {e}")
