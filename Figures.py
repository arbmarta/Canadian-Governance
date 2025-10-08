import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path

## ------------------------------------------------- FIGURE FILE PATHS -------------------------------------------------
#region

FIGURE_DIR = Path("Figures")
FIGURE_DIR.mkdir(exist_ok=True)  # create folder if it doesn't exist

REG_BODY_FIG = FIGURE_DIR / "Figure 1: Regulatory Bodies.pdf"
PROF_ASSOC_FIG = FIGURE_DIR / "Figure 2: Arboricultural Governance.pdf"
RIGHT_TO_PRACTICE_FIG = FIGURE_DIR / "Figure 3: Right to Practice.pdf"

#endregion

## ------------------------------------------------- IMPORT SHAPEFILE --------------------------------------------------
#region

gdf = gpd.read_file("Shapefile/Provinces.gpkg")

# Standardize province codes
mapping = {"N.L.": "NL", "P.E.I.": "PE", "N.S.": "NS", "N.B.": "NB",
           "Que.": "QC", "Ont.": "ON", "Man.": "MB", "Sask.": "SK",
           "Alta.": "AB", "B.C.": "BC", "Y.T.": "YT", "N.W.T.": "NT", "Nvt.": "NU"}
gdf["PREABBR"] = gdf["PREABBR"].replace(mapping)

#endregion

## ---------------------------------------------- REGULATORY BODY FIGURE -----------------------------------------------
if not REG_BODY_FIG.exists():
    categories = {
        "Regulatory Body": ['NL', 'NS', 'NB', 'QC', 'ON', 'SK', 'AB', 'BC'],
        "Right to Title": ['NL', 'NS', 'NB', 'QC', 'ON', 'SK', 'AB', 'BC'],
        "Right to Practice": ['QC', 'ON', 'SK', 'AB', 'BC'],
    }

    fig, axes = plt.subplots(1, 3, figsize=(14, 12))
    axes = axes.flatten()

    for i, (title, provinces) in enumerate(categories.items()):
        gdf["color"] = gdf["PREABBR"].apply(lambda x: "#1f78b4" if x in provinces else "#ffffff")
        gdf.plot(color=gdf["color"], edgecolor="black", ax=axes[i])
        axes[i].set_title(title, fontsize=14)
        axes[i].axis("off")

    plt.tight_layout()
    fig.savefig(REG_BODY_FIG)
    plt.close(fig)

## ----------------------------------------- PROFESSIONAL ASSOCIATIONS FIGURE ------------------------------------------
if not PROF_ASSOC_FIG.exists():
    categories = {
        "Professional Associations": ['NL', 'NS', 'PE', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC'],
        "ISA Chapters": ['NL', 'NS', 'PE', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC'],
        "Apprenticeship & Skilled Trades Agencies": ['NS', 'NB', 'QC', 'ON', 'BC'],
        "Other Arboricultural Governance Orgs": ['BC', 'MB', 'ON']
    }

    isa_map = {
        "BC": "#1b9e77",
        "AB": "#d95f02", "SK": "#d95f02", "MB": "#d95f02",
        "ON": "#7570b3",
        "QC": "#e7298a",
        "NB": "#66a61e", "NS": "#66a61e", "PE": "#66a61e", "NL": "#66a61e"
    }
    gdf["isa_color"] = gdf["PREABBR"].map(isa_map).fillna("#ffffff")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for i, (title, provinces) in enumerate(categories.items()):
        gdf["color"] = gdf["PREABBR"].apply(lambda x: "#1f78b4" if x in provinces else "#ffffff")
        gdf.plot(color=gdf["color"], edgecolor="black", ax=axes[i])
        axes[i].set_title(title, fontsize=14)
        axes[i].axis("off")

    plt.tight_layout()
    fig.savefig(PROF_ASSOC_FIG)
    plt.close(fig)

## --------------------------------------------- RIGHT TO PRACTICE FIGURE ----------------------------------------------
if not RIGHT_TO_PRACTICE_FIG.exists():
    categories = {
        "Right to Practice: Urban Forestry": ['BC', 'ON', 'QC'],
        "Right to Practice: Urban Forestry": ['SK', 'MB']
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 12))
    axes = axes.flatten()

    for i, (title, provinces) in enumerate(categories.items()):
        gdf["color"] = gdf["PREABBR"].apply(lambda x: "#1f78b4" if x in provinces else "#ffffff")
        gdf.plot(color=gdf["color"], edgecolor="black", ax=axes[i])
        axes[i].set_title(title, fontsize=14)
        axes[i].axis("off")

    plt.tight_layout()
    fig.savefig(RIGHT_TO_PRACTICE_FIG)
    plt.close(fig)