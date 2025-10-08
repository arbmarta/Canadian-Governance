import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path

## ------------------------------------------------- SETTINGS -------------------------------------------------
USE_SIMPLIFIED = True  # Set to False to use original shapefile

## ------------------------------------------------- FIGURE FILE PATHS -------------------------------------------------
FIGURE_DIR = Path("Figures")
FIGURE_DIR.mkdir(exist_ok=True)

REG_BODY_FIG = FIGURE_DIR / "Figure 1: Regulatory Bodies.pdf"
PROF_ASSOC_FIG = FIGURE_DIR / "Figure 2: Arboricultural Governance.pdf"
RIGHT_TO_PRACTICE_FIG = FIGURE_DIR / "Figure 3: Right to Practice.pdf"

## ------------------------------------------------- IMPORT SHAPEFILE --------------------------------------------------
# Determine which shapefile to use
shapefile_path = "Shapefile/Provinces_simplified.gpkg" if USE_SIMPLIFIED else "Shapefile/Provinces.gpkg"
gdf = gpd.read_file(shapefile_path)

# Standardize province codes
mapping = {"N.L.": "NL", "P.E.I.": "PE", "N.S.": "NS", "N.B.": "NB",
           "Que.": "QC", "Ont.": "ON", "Man.": "MB", "Sask.": "SK",
           "Alta.": "AB", "B.C.": "BC", "Y.T.": "YT", "N.W.T.": "NT", "Nvt.": "NU"}
gdf["PREABBR"] = gdf["PREABBR"].replace(mapping)

## ---------------------------------------------- HELPER FUNCTION -----------------------------------------------
def assign_colors(gdf, provinces, color_active="#1f78b4", color_inactive="#ffffff"):
    return gdf["PREABBR"].isin(provinces).map({True: color_active, False: color_inactive})

## ---------------------------------------------- REGULATORY BODY FIGURE -----------------------------------------------
if not REG_BODY_FIG.exists():
    categories = {
        "Forestry Professional \nRegulatory Organizations": ['NL', 'NS', 'NB', 'QC', 'ON', 'SK', 'AB', 'BC'],
        "Right to Title Legislation": ['NL', 'NS', 'NB', 'QC', 'ON', 'SK', 'AB', 'BC'],
        "Right to Practice Legislation": ['QC', 'ON', 'SK', 'AB', 'BC'],
    }

    fig, axes = plt.subplots(1, 3, figsize=(14, 12))

    for ax, (title, provinces) in zip(axes, categories.items()):
        colors = assign_colors(gdf, provinces)
        gdf.plot(color=colors, edgecolor="black", ax=ax, linewidth=0.5)
        ax.set_title(title, fontsize=14)
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(REG_BODY_FIG, dpi=450)  # Added dpi for better quality
    plt.close(fig)
    print(f"Saved: {REG_BODY_FIG}")

## ----------------------------------------- PROFESSIONAL ASSOCIATIONS FIGURE ------------------------------------------
if not PROF_ASSOC_FIG.exists():
    categories = {
        "Professional Associations": ['NL', 'NS', 'PE', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC'],
        "ISA Chapters": ['NL', 'NS', 'PE', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC'],
        "Apprenticeship & Skilled Trades Agencies": ['NS', 'NB', 'QC', 'ON', 'BC'],
        "Other Arboricultural Governance Orgs": ['BC', 'MB', 'ON']
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for ax, (title, provinces) in zip(axes, categories.items()):
        colors = assign_colors(gdf, provinces)
        gdf.plot(color=colors, edgecolor="black", ax=ax, linewidth=0.5)
        ax.set_title(title, fontsize=14)
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(PROF_ASSOC_FIG, dpi=450)
    plt.close(fig)
    print(f"Saved: {PROF_ASSOC_FIG}")

## --------------------------------------------- RIGHT TO PRACTICE FIGURE ----------------------------------------------
if not RIGHT_TO_PRACTICE_FIG.exists():
    categories = {
        "Right to Practice: Urban Forestry": ['BC', 'ON', 'QC'],
        "Right to Practice: Rural Forestry": ['SK', 'MB']  # Fixed: was duplicate title
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 12))

    for ax, (title, provinces) in zip(axes, categories.items()):
        colors = assign_colors(gdf, provinces)
        gdf.plot(color=colors, edgecolor="black", ax=ax, linewidth=0.5)
        ax.set_title(title, fontsize=14)
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(RIGHT_TO_PRACTICE_FIG, dpi=450)
    plt.close(fig)
    print(f"Saved: {RIGHT_TO_PRACTICE_FIG}")