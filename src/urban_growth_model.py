"""
Urban Growth Modeling & Future Trend Forecasting (2025 - 2035)
Includes:
1. Spatial Inequality Indices (Gini Coefficient & Lorenz Curve formulation)
2. Historical Transition Dynamics (2000 -> 2010 -> 2020)
3. Logistic Expansion & Carrying Capacity Simulation (2025, 2030, 2035)
"""

import os
import json
import numpy as np

INPUT_METRICS_PATH = "data/processed/mumbai_ward_inequality.json"
OUTPUT_PROJECTIONS_PATH = "data/processed/mumbai_growth_projections_2025_2035.json"

def calculate_gini(values: list) -> float:
    """
    Computes Gini Coefficient for measuring spatial inequality across wards.
    0 = Perfect spatial equality, 1 = Complete spatial inequality.
    """
    arr = np.array(values, dtype=np.float64)
    # Shift if min is negative (e.g. NDVI could have small negative values for water)
    if np.amin(arr) < 0:
        arr -= np.amin(arr)
    arr += 1e-7 # Prevent division by zero
    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    gini = (2.0 * np.sum(index * arr)) / (n * np.sum(arr)) - (n + 1.0) / n
    return float(round(gini, 4))

def logistic_growth_step(b_current, r, carrying_capacity, dt=1.0):
    """
    Single step of logistic urban growth differential equation:
    dB/dt = r * B * (1 - B / K)
    """
    growth = r * b_current * (1.0 - (b_current / carrying_capacity)) * dt
    return min(carrying_capacity, max(b_current, b_current + growth))

def model_urban_growth():
    if not os.path.exists(INPUT_METRICS_PATH):
        raise FileNotFoundError(f"Missing {INPUT_METRICS_PATH}. Run spatial_inequality.py first.")

    with open(INPUT_METRICS_PATH, "r", encoding="utf-8") as f:
        ward_data = json.load(f)

    print(f"[*] Loaded data for {len(ward_data)} Mumbai BMC administrative wards.")

    # 1. Inequality Metrics Calculation
    green_values = [w["ndvi_greenery"] for w in ward_data]
    ntl_values = [w["nighttime_lights"] for w in ward_data]
    econ_per_capita_values = [w["economic_intensity_proxy"] for w in ward_data]
    built_2020_values = [w["built_up_2020"] for w in ward_data]

    green_gini = calculate_gini(green_values)
    ntl_gini = calculate_gini(ntl_values)
    econ_gini = calculate_gini(econ_per_capita_values)
    built_gini = calculate_gini(built_2020_values)

    print("\n================ SPATIAL INEQUALITY SUMMARY ================")
    print(f"  * Green Cover Disparity (NDVI Gini)      : {green_gini:.4f}")
    print(f"  * Economic Radiance Disparity (NTL Gini) : {ntl_gini:.4f}")
    print(f"  * Per-Capita Economic Disparity Gini     : {econ_gini:.4f}")
    print(f"  * Built-up Spatial Concentration Gini    : {built_gini:.4f}")
    print("============================================================\n")

    # 2. Fit Growth Models & Forecast 2025, 2030, 2035 per Ward
    projections = []
    
    for w in ward_data:
        ward_name = w["ward"]
        b00 = max(1.0, w["built_up_2000"])
        b10 = max(b00, w["built_up_2010"])
        b20 = max(b10, w["built_up_2020"])

        # Estimate carrying capacity (K) for this ward:
        # In Mumbai, maximum build-out observed is ~4000 m² per 100m grid (Ward C: 3863 m²)
        # Saturated island city wards have limited capacity headroom (~5-10% vertical expansion)
        # Suburbs (Malad, Govandi, Borivali, Bhandup) have more developable brownfield/periphery land
        if b20 >= 3000.0:
            K = min(4200.0, b20 * 1.08)  # Saturated / high-density
        elif b20 >= 2000.0:
            K = min(3600.0, b20 * 1.25)  # Established suburbs
        else:
            K = min(3000.0, max(b20 * 1.45, 1800.0))  # High-growth outer suburbs

        # Calibrate intrinsic growth rate (r) from 2000-2020 trajectory
        # Continuous compounding rate: r ≈ (ln(b20) - ln(b00)) / 20
        delta_log = np.log(b20) - np.log(b00)
        raw_r = delta_log / 20.0
        r_rate = max(0.001, min(0.05, raw_r))

        # Simulate 2020 to 2025 (5 years)
        b25 = b20
        for _ in range(5):
            b25 = logistic_growth_step(b25, r_rate, K, dt=1.0)

        # Simulate 2025 to 2030 (5 years)
        b30 = b25
        for _ in range(5):
            b30 = logistic_growth_step(b30, r_rate, K, dt=1.0)

        # Simulate 2030 to 2035 (5 years)
        b35 = b30
        for _ in range(5):
            b35 = logistic_growth_step(b35, r_rate, K, dt=1.0)

        # Compute saturation percentage
        saturation_2020 = (b20 / K) * 100.0
        saturation_2035 = (b35 / K) * 100.0

        # Projected vegetation impact: As built-up approaches K, NDVI decays proportionally
        decay_factor = (b30 - b20) / K
        predicted_ndvi_2030 = max(0.08, w["ndvi_greenery"] * (1.0 - (0.4 * decay_factor)))

        # Growth classification
        if r_rate >= 0.005 and (b35 - b20) > 100.0:
            growth_class = "High Expansion Suburb"
        elif r_rate >= 0.002:
            growth_class = "Moderate Growth Corridor"
        else:
            growth_class = "Saturated / Infill Only"

        projections.append({
            "ward": ward_name,
            "historical": {
                "2000": round(b00, 2),
                "2010": round(b10, 2),
                "2020": round(b20, 2)
            },
            "predicted": {
                "2025": round(b25, 2),
                "2030": round(b30, 2),
                "2035": round(b35, 2)
            },
            "annual_growth_rate_pct": round(float(r_rate * 100.0), 2),
            "carrying_capacity_K": round(float(K), 2),
            "saturation_2020_pct": round(float(saturation_2020), 1),
            "saturation_2035_pct": round(float(saturation_2035), 1),
            "ndvi_current": w["ndvi_greenery"],
            "ndvi_predicted_2030": round(float(predicted_ndvi_2030), 4),
            "growth_pressure_class": growth_class
        })

    # Sort by projected growth from 2020 to 2035
    projections.sort(key=lambda x: (x["predicted"]["2035"] - x["historical"]["2020"]), reverse=True)

    result_payload = {
        "metadata": {
            "city": "Mumbai",
            "region": "BMC 24 Administrative Wards",
            "model_type": "Logistic Urban Expansion & Spatial Inequality Transition Model",
            "base_epochs": [2000, 2010, 2020],
            "forecast_epochs": [2025, 2030, 2035]
        },
        "inequality_indices": {
            "green_disparity_gini": green_gini,
            "economic_radiance_gini": ntl_gini,
            "per_capita_economic_gini": econ_gini,
            "built_up_concentration_gini": built_gini
        },
        "ward_projections": projections
    }

    os.makedirs(os.path.dirname(OUTPUT_PROJECTIONS_PATH), exist_ok=True)
    with open(OUTPUT_PROJECTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)

    print(f"[SUCCESS] Growth forecast model complete! Saved to {OUTPUT_PROJECTIONS_PATH}")
    print("\n--- TOP 5 WARDS WITH HIGHEST PROJECTED URBAN EXPANSION (2020 - 2035) ---")
    for p in projections[:5]:
        growth = p["predicted"]["2035"] - p["historical"]["2020"]
        print(f"  Ward {p['ward']:<5}: 2020={p['historical']['2020']} -> 2035={p['predicted']['2035']} (Delta: +{growth:.1f}) [{p['growth_pressure_class']}]")

    print("\n--- TOP 3 SATURATED WARDS (LITTLE HORIZONTAL ROOM, VERTICAL REDEVELOPMENT ONLY) ---")
    saturated = [p for p in projections if p["growth_pressure_class"] == "Saturated / Redevelopment"]
    for p in saturated[:3]:
        print(f"  Ward {p['ward']:<5}: Saturation={p['saturation_2020_pct']}% -> 2035={p['saturation_2035_pct']}%")

    return result_payload

if __name__ == "__main__":
    model_urban_growth()
