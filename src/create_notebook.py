"""
Script to programmatically generate the interactive research Jupyter notebook:
notebooks/mumbai_urban_growth_inequality.ipynb
"""

import json
import os

NOTEBOOK_PATH = "notebooks/mumbai_urban_growth_inequality.ipynb"

def create_notebook():
    os.makedirs(os.path.dirname(NOTEBOOK_PATH), exist_ok=True)
    
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🌆 Mumbai Urban Growth & Spatial Inequality Atlas\n",
                "### Modeling 25-Year Urban Transitions (2000–2025) & Forecasting to 2035 via Google Earth Engine\n",
                "\n",
                "**Project ID**: `maximal-dynamo-506718-g8`  \n",
                "**Data Sources**:\n",
                "- **GHSL (Global Human Settlement Layer)**: Multi-temporal built-up grids (2000, 2010, 2020)\n",
                "- **Copernicus Sentinel-2**: Cloud-free pre-monsoon multispectral indices (NDVI green cover & NDBI built index)\n",
                "- **NOAA VIIRS Nighttime Lights**: Annual radiance as an economic activity proxy\n",
                "- **WorldPop**: Gridded population density per 100m pixel\n",
                "- **BMC Mumbai Administrative Spatial Boundaries**: 24 Municipal Wards"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Setup & Environment Verification\n",
                "Verify Google Earth Engine connection and load key libraries."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import json\n",
                "import ee\n",
                "import numpy as np\n",
                "import folium\n",
                "from IPython.display import display, HTML, Image\n",
                "\n",
                "# Initialize Earth Engine\n",
                "PROJECT_ID = 'maximal-dynamo-506718-g8'\n",
                "try:\n",
                "    ee.Initialize(project=PROJECT_ID)\n",
                "    print('✅ Google Earth Engine connected successfully!')\n",
                "except Exception as e:\n",
                "    print(f'Authentication required: {e}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Load Processed Spatial Inequality Metrics\n",
                "Load the zonal statistics computed in Earth Engine across all 24 Mumbai BMC wards."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "with open('../data/processed/mumbai_ward_inequality.json', 'r', encoding='utf-8') as f:\n",
                "    ward_metrics = json.load(f)\n",
                "\n",
                "print(f'Loaded zonal data for {len(ward_metrics)} administrative wards.')\n",
                "\n",
                "# Print summary table of extreme wards\n",
                "sorted_by_green = sorted(ward_metrics, key=lambda x: x['ndvi_greenery'])\n",
                "print('=== GREEN COVER DEFICIT WARDS (Low NDVI) ===')\n",
                "for w in sorted_by_green[:5]:\n",
                "    print(f\"  Ward {w['ward']:<5}: NDVI = {w['ndvi_greenery']:<6} | Built-up = {w['built_up_2020']} m² | NTL = {w['nighttime_lights']} nW\")\n",
                "\n",
                "print('\\n=== GREEN COVER SURPLUS WARDS (High NDVI) ===')\n",
                "for w in sorted_by_green[-5:]:\n",
                "    print(f\"  Ward {w['ward']:<5}: NDVI = {w['ndvi_greenery']:<6} | Built-up = {w['built_up_2020']} m² | NTL = {w['nighttime_lights']} nW\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Spatial Inequality & Lorenz Distribution Curves\n",
                "Evaluate the Gini coefficients for Green Cover Disparity, Economic Radiance, and Built-up Concentration."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "with open('../data/processed/mumbai_growth_projections_2025_2035.json', 'r', encoding='utf-8') as f:\n",
                "    projections = json.load(f)\n",
                "\n",
                "gini = projections['inequality_indices']\n",
                "print('--- GINI COEFFICIENT RESULTS ---')\n",
                "for k, v in gini.items():\n",
                "    print(f\"  {k.replace('_', ' ').title()}: {v:.4f}\")\n",
                "\n",
                "# Display Lorenz Curve\n",
                "Image(filename='../reports/figures/lorenz_inequality_curve.png')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Green Deficit vs Economic Activity Intensity\n",
                "Examining the stark spatial trade-off between economic clustering (high nighttime lights in South/Island Mumbai) vs vegetative canopy in suburban buffers."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "Image(filename='../reports/figures/spatial_inequality_ranking.png')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Model Accuracy & Historical Backtesting\n",
                "Evaluating model predictive power using **10-Year Blind Historical Backtesting**:\n",
                "- Model trained strictly on **2000 -> 2010** satellite observations.\n",
                "- Asked to simulate 10 years forward to **2020** without seeing 2020 ground truth.\n",
                "- Predictions benchmarked against actual **GHSL 2020** satellite data across all 24 wards."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "with open('../reports/model_validation_report.json', 'r', encoding='utf-8') as f:\n",
                "    val_report = json.load(f)\n",
                "\n",
                "metrics = val_report['overall_metrics']\n",
                "print('==================== MODEL ACCURACY METRICS ====================')\n",
                "print(f\"  R² Score (Goodness of Fit) : {metrics['r2_score']}\")\n",
                "print(f\"  Overall Predictive Accuracy : {metrics['predictive_accuracy_pct']}%\")\n",
                "print(f\"  Mean Abs. Percentage Error  : {metrics['mean_absolute_percentage_error_mape']}%\")\n",
                "print(f\"  Root Mean Squared Error     : {metrics['root_mean_squared_error_rmse']} m²\")\n",
                "print('================================================================')\n",
                "\n",
                "# Display Backtest Scatter Validation Plot\n",
                "Image(filename='../reports/figures/model_accuracy_validation.png')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Urban Growth Projections (2000 to 2035)\n",
                "Plotting historical GHSL trajectories (2000, 2010, 2020) and simulated future expansion curves (2025, 2030, 2035)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "Image(filename='../reports/figures/urban_growth_trajectories.png')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Interactive Geospatial Atlas\n",
                "Explore the interactive multi-layer map of Mumbai's 24 wards with rich attribute popups."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Display interactive Folium map inline inside notebook\n",
                "from IPython.display import IFrame\n",
                "IFrame(src='../reports/mumbai_interactive_map.html', width='100%', height=650)"
            ]
        }
    ]

    notebook_json = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (.venv)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11.9"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook_json, f, indent=2)

    print(f"[SUCCESS] Interactive Jupyter Notebook generated: {NOTEBOOK_PATH}")

if __name__ == "__main__":
    create_notebook()
