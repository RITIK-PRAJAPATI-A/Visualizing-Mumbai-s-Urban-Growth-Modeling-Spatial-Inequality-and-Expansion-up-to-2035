"""
Interactive Geospatial & Analytical Visualizer for Mumbai Urban Growth & Spatial Inequality
Outputs:
1. reports/mumbai_interactive_map.html (Multi-layer Leaflet interactive map with popups)
2. reports/figures/spatial_inequality_ranking.png
3. reports/figures/urban_growth_trajectories.png
4. reports/figures/lorenz_inequality_curve.png
"""

import os
import json
import folium
from folium import plugins
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

WARDS_GEOJSON_PATH = "data/raw/mumbai_bmc_wards.geojson"
PROJECTIONS_PATH = "data/processed/mumbai_growth_projections_2025_2035.json"
INEQUALITY_PATH = "data/processed/mumbai_ward_inequality.json"
REPORTS_DIR = "reports"
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

WARD_LOCALITIES = {
    "A": "Colaba, Fort, Nariman Point, Churchgate",
    "B": "Sandhurst Road, Dongri, Masjid Bunder",
    "C": "Marine Lines, Girgaon, Bhuleshwar, Kalbadevi",
    "D": "Malabar Hill, Walkeshwar, Cumballa Hill",
    "E": "Byculla, Mazgaon, Mumbai Central",
    "F/S": "Parel, Sewri, Naigaon",
    "F/N": "Matunga, Sion, Wadala",
    "G/S": "Worli, Lower Parel, Prabhadevi",
    "G/N": "Dadar, Mahim, Dharavi",
    "H/W": "Bandra West, Khar West, Santacruz West",
    "H/E": "Bandra East, BKC, Santacruz East",
    "K/W": "Andheri West, Juhu, Versova, Lokhandwala",
    "K/E": "Andheri East, Vile Parle East, MIDC, Airport",
    "L": "Kurla, Sakinaka, Asalpha",
    "M/E": "Govandi, Mankhurd, Shivaji Nagar",
    "M/W": "Chembur, Tilak Nagar, Mahul",
    "N": "Ghatkopar, Vikhroli East/West",
    "P/S": "Goregaon East/West",
    "P/N": "Malad, Marve, Madh Island",
    "R/S": "Kandivali, Charkop, Lokhandwala Twp",
    "R/C": "Borivali, Gorai, SGNP Buffer",
    "R/N": "Dahisar East/West",
    "S": "Bhandup, Powai, IIT Bombay, Kanjurmarg",
    "T": "Mulund East/West, Nahur"
}

def generate_interactive_map():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    with open(WARDS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        wards_geo = json.load(f)
        
    with open(PROJECTIONS_PATH, "r", encoding="utf-8") as f:
        model_results = json.load(f)
        
    projections_dict = {p["ward"]: p for p in model_results["ward_projections"]}
    
    # Initialize Folium Map centered on Mumbai
    mumbai_center = [19.0760, 72.8777]
    m = folium.Map(
        location=mumbai_center,
        zoom_start=11,
        tiles=None,
        control_scale=True
    )

    # Reliable Basemap 1: Esri World Street Map (crisp, detailed, no API key, allows local file:/// access)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS",
        name="🗺️ Street Map (Esri)",
        control=True
    ).add_to(m)

    # Reliable Basemap 2: Esri World Light Gray (clean, minimalistic for thematic inequality layers)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        name="🏙️ Light Gray Canvas (Esri)",
        control=True
    ).add_to(m)

    # Reliable Basemap 3: Esri World Imagery (high-res satellite background)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics",
        name="🛰️ Satellite Imagery (Esri)",
        control=True
    ).add_to(m)

    # Style function for NDVI Green Cover
    def style_green(feature):
        ward = feature["properties"].get("name")
        p = projections_dict.get(ward, {})
        val = p.get("ndvi_current", 0.2)
        # Colormap: low NDVI (deficit) -> red/orange, high NDVI -> lush green
        if val < 0.15:
            color = "#d73027"
        elif val < 0.20:
            color = "#fc8d59"
        elif val < 0.25:
            color = "#fee08b"
        elif val < 0.35:
            color = "#a6d96a"
        else:
            color = "#1a9850"
        return {
            "fillColor": color,
            "color": "#333333",
            "weight": 1.2,
            "fillOpacity": 0.65
        }

    # Style function for Projected Urban Growth Delta (2020 - 2035)
    def style_growth(feature):
        ward = feature["properties"].get("name")
        p = projections_dict.get(ward, {})
        delta = p.get("predicted", {}).get("2035", 0) - p.get("historical", {}).get("2020", 0)
        # Colormap: high expansion -> deep purple/indigo, low expansion -> pale yellow
        if delta >= 40.0:
            color = "#49006a"
        elif delta >= 30.0:
            color = "#7a0177"
        elif delta >= 20.0:
            color = "#ae017e"
        elif delta >= 10.0:
            color = "#dd3497"
        else:
            color = "#fcc5c0"
        return {
            "fillColor": color,
            "color": "#222222",
            "weight": 1.2,
            "fillOpacity": 0.70
        }

    # Custom Tooltip & Popup Builder
    for feature in wards_geo["features"]:
        ward = feature["properties"].get("name")
        p = projections_dict.get(ward, {})
        hist = p.get("historical", {})
        pred = p.get("predicted", {})
        localities = WARD_LOCALITIES.get(ward, "Mumbai Locality")
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 260px; font-size: 13px;">
            <h3 style="margin: 0 0 4px 0; color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 3px;">
                Ward {ward}
            </h3>
            <p style="margin: 2px 0 8px 0; font-size: 11px; color: #4b5563; font-style: italic;">
                {localities}
            </p>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <tr style="background: #f3f4f6;">
                    <td style="padding: 3px;"><b>Vegetation (NDVI):</b></td>
                    <td style="padding: 3px; text-align: right; font-weight: bold; color: {'#16a34a' if p.get('ndvi_current', 0) > 0.25 else '#dc2626'};">
                        {p.get('ndvi_current', 'N/A')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Built-up 2000:</b></td>
                    <td style="padding: 3px; text-align: right;">{hist.get('2000', 0)} m²</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 3px;"><b>Built-up 2020:</b></td>
                    <td style="padding: 3px; text-align: right;">{hist.get('2020', 0)} m²</td>
                </tr>
                <tr style="border-top: 1px dashed #9ca3af; background: #eff6ff;">
                    <td style="padding: 3px;"><b>Predicted 2030:</b></td>
                    <td style="padding: 3px; text-align: right; font-weight: bold;">{pred.get('2030', 0)} m²</td>
                </tr>
                <tr style="background: #eff6ff;">
                    <td style="padding: 3px;"><b>Predicted 2035:</b></td>
                    <td style="padding: 3px; text-align: right; font-weight: bold; color: #7e22ce;">{pred.get('2035', 0)} m²</td>
                </tr>
                <tr style="border-top: 1px solid #d1d5db;">
                    <td style="padding: 3px;"><b>Status:</b></td>
                    <td style="padding: 3px; text-align: right; font-weight: bold; font-size: 11px;">
                        {p.get('growth_pressure_class', 'N/A')}
                    </td>
                </tr>
            </table>
        </div>
        """
        feature["properties"]["popup"] = popup_html

    # Layer 1: Green Cover & Disparity (NDVI)
    layer_green = folium.GeoJson(
        wards_geo,
        name="🌱 Spatial Inequality: Green Cover (NDVI)",
        style_function=style_green,
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Ward: "]),
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False)
    )
    layer_green.add_to(m)

    # Layer 2: Predicted Urban Expansion to 2035
    layer_growth = folium.GeoJson(
        wards_geo,
        name="🏗️ Predicted Urban Expansion (2020 - 2035)",
        style_function=style_growth,
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Ward: "]),
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False),
        show=False
    )
    layer_growth.add_to(m)

    # Add Layer Control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add Title Banner
    title_html = """
    <div style="position: fixed; top: 12px; left: 70px; z-index: 1000; background: white; 
                padding: 10px 16px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
                border: 1px solid #d1d5db; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <h4 style="margin: 0; color: #1e3a8a; font-size: 15px; font-weight: 700;">Mumbai Urban Growth & Inequality Atlas</h4>
        <p style="margin: 2px 0 0 0; color: #4b5563; font-size: 11px;">
            Google Earth Engine (GHSL, Sentinel-2, VIIRS) • 24 BMC Wards
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Auto-fit map viewport to Mumbai BMC Ward boundaries
    m.fit_bounds(layer_green.get_bounds())

    output_html_path = os.path.join(REPORTS_DIR, "mumbai_interactive_map.html")
    m.save(output_html_path)
    print(f"[SUCCESS] Interactive Folium map generated: {output_html_path}")

def generate_analytical_charts():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    
    with open(INEQUALITY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(PROJECTIONS_PATH, "r", encoding="utf-8") as f:
        proj_data = json.load(f)

    # Chart 1: Green Cover Disparity vs Economic Radiance (Ranked)
    plt.figure(figsize=(14, 7))
    sorted_by_green = sorted(data, key=lambda x: x["ndvi_greenery"])
    wards = [d["ward"] for d in sorted_by_green]
    green = [d["ndvi_greenery"] for d in sorted_by_green]
    ntl = [d["nighttime_lights"] for d in sorted_by_green]

    x = np.arange(len(wards))
    width = 0.40

    fig, ax1 = plt.subplots(figsize=(14, 6))
    color_green = "#2ca02c"
    ax1.set_xlabel("BMC Administrative Wards (Sorted by Green Cover Deficit -> Surplus)", fontweight="bold")
    ax1.set_ylabel("NDVI Green Cover Index (Jan-Apr 2023)", color=color_green, fontweight="bold")
    bars1 = ax1.bar(x - width/2, green, width, label="Greenery (NDVI)", color=color_green, alpha=0.85)
    ax1.tick_params(axis='y', labelcolor=color_green)
    ax1.set_xticks(x)
    ax1.set_xticklabels(wards, rotation=45, ha="right")
    ax1.grid(axis='y', linestyle='--', alpha=0.3)

    ax2 = ax1.twinx()
    color_ntl = "#ff7f0e"
    ax2.set_ylabel("Nighttime Light Radiance (nW/cm²/sr - Economic Activity)", color=color_ntl, fontweight="bold")
    bars2 = ax2.bar(x + width/2, ntl, width, label="Nighttime Lights (VIIRS)", color=color_ntl, alpha=0.85)
    ax2.tick_params(axis='y', labelcolor=color_ntl)

    plt.title("Spatial Inequality in Mumbai: Green Space Deficit vs Economic Activity Intensity", fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    chart1_path = os.path.join(FIGURES_DIR, "spatial_inequality_ranking.png")
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Chart 1 saved: {chart1_path}")

    # Chart 2: Historical vs Predicted Trajectories (2000 - 2035)
    plt.figure(figsize=(12, 6))
    projections = proj_data["ward_projections"]
    years = [2000, 2010, 2020, 2025, 2030, 2035]

    # Pick contrast wards: Saturated Island City (C, B, A), Established Suburbs (H/W, K/E), Fast Expanding (P/N, M/E, R/C)
    contrast_wards = ["C", "B", "A", "H/W", "K/E", "P/N", "M/E", "R/C", "S", "T"]
    colors = plt.cm.tab10(np.linspace(0, 1, len(contrast_wards)))

    for i, target in enumerate(contrast_wards):
        match = next((p for p in projections if p["ward"] == target), None)
        if match:
            h = match["historical"]
            p = match["predicted"]
            y_vals = [h["2000"], h["2010"], h["2020"], p["2025"], p["2030"], p["2035"]]
            style = "-" if i < 5 else "--"
            plt.plot(years[:3], y_vals[:3], marker="o", linestyle="-", color=colors[i], label=f"Ward {target} ({WARD_LOCALITIES.get(target, '').split(',')[0]})", linewidth=2)
            plt.plot(years[2:], y_vals[2:], marker="s", linestyle=":", color=colors[i], linewidth=2)

    plt.axvline(x=2020, color="gray", linestyle="--", alpha=0.7, label="Forecast Horizon (2020)")
    plt.title("Urban Built-Up Surface Trajectories (2000 - 2035) Across Mumbai Wards", fontsize=13, fontweight="bold")
    plt.xlabel("Year", fontweight="bold")
    plt.ylabel("Built-Up Surface Area (m² per 100m grid cell)", fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    plt.tight_layout()
    chart2_path = os.path.join(FIGURES_DIR, "urban_growth_trajectories.png")
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Chart 2 saved: {chart2_path}")

    # Chart 3: Lorenz Inequality Curve
    plt.figure(figsize=(7, 7))
    for key, label, col in [
        ("ndvi_greenery", f"Green Space Access (Gini = {proj_data['inequality_indices']['green_disparity_gini']:.3f})", "#2ca02c"),
        ("nighttime_lights", f"Economic Radiance (Gini = {proj_data['inequality_indices']['economic_radiance_gini']:.3f})", "#ff7f0e"),
        ("built_up_2020", f"Built-up Concentration (Gini = {proj_data['inequality_indices']['built_up_concentration_gini']:.3f})", "#1f77b4")
    ]:
        vals = np.sort([d[key] for d in data])
        vals = vals - np.min(vals) + 1e-5
        cum_vals = np.cumsum(vals) / np.sum(vals)
        cum_pop = np.linspace(0, 1, len(vals))
        plt.plot(np.insert(cum_pop, 0, 0), np.insert(cum_vals, 0, 0), label=label, color=col, linewidth=2.2)

    plt.plot([0, 1], [0, 1], "k--", label="Line of Perfect Equality (Gini = 0.0)", alpha=0.7)
    plt.title("Lorenz Curves: Spatial Inequality in Mumbai (24 Wards)", fontsize=13, fontweight="bold")
    plt.xlabel("Cumulative Fraction of Administrative Wards", fontweight="bold")
    plt.ylabel("Cumulative Fraction of Attribute", fontweight="bold")
    plt.legend(loc="upper left", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    chart3_path = os.path.join(FIGURES_DIR, "lorenz_inequality_curve.png")
    plt.savefig(chart3_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Chart 3 saved: {chart3_path}")

if __name__ == "__main__":
    generate_interactive_map()
    generate_analytical_charts()
