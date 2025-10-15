import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.patches import Patch

# Load shapefile / geopackage
provinces = gpd.read_file('Shapefile/Simplified provinces - 10 km.gpkg')

# Province acronyms mapping (same as you had)
province_accronyms = {
    'Newfoundland and Labrador / Terre-Neuve-et-Labrador': 'NL',
    'Prince Edward Island / Île-du-Prince-Édouard': 'PE',
    'Nova Scotia / Nouvelle-Écosse': 'NS',
    'New Brunswick / Nouveau-Brunswick': 'NB',
    'Quebec / Québec': 'QC',
    'Ontario': 'ON',
    'Manitoba': 'MB',
    'Saskatchewan': 'SK',
    'Alberta': 'AB',
    'British Columbia / Colombie-Britannique': 'BC',
    'Yukon': 'YT',
    'Northwest Territories / Territoires du Nord-Ouest': 'NT',
    'Nunavut': 'NU'
}

# Figure items (same structure)
class Figure2:
    class RegulatoryBodies:
        forestry = ['AB', 'SK', 'NL', 'PE', 'NS', 'NB']
        urban_forestry = ['BC', 'ON', 'QC']

    class RightToTitle:
        forestry = ['AB', 'SK', 'NL', 'PE', 'NS', 'NB', 'BC', 'ON', 'QC']
        arboriculture = ['MB']

    class RightToPractice:
        forestry = ['AB', 'SK', 'BC', 'ON', 'QC']
        urban_forestry = ['BC', 'ON', 'QC']
        arboriculture = ['MB', 'SK']

# Map province names to acronyms
provinces['ACRONYM'] = provinces['PRNAME'].map(province_accronyms)

# Some handy constants
atlantic = {'NL', 'PE', 'NS', 'NB'}

# subplot layout: 1 row x 3 cols
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Define the groups (name, (list of subgroup-name, list of acronyms, colour)) for each of the 3 panels
panel_specs = [
    # Regulatory Bodies: forestry vs urban forestry
    (
        "Professional Regulatory Organizations (PROs)",
        [
            ("Forestry PROs", Figure2.RegulatoryBodies.forestry, "#4C72B0"),      # blue-ish
            ("Forestry PROs Engaged in Urban Forestry", Figure2.RegulatoryBodies.urban_forestry, "#DD8452"),  # orange-ish
        ],
    ),
    # Right to Title: forestry vs arboriculture
    (
        "Right to Title",
        [
            ("Right to Title for Arborists", Figure2.RightToTitle.arboriculture, "#C44E52"),  # red
            ("Right to Title for RPFs", Figure2.RightToTitle.forestry, "#55A868"),  # green
        ],
    ),
    # Right to Practice: forestry vs urban forestry vs arboriculture
    (
        "Right to Practice Arboriculture and Urban Forestry",
        [
            ("Right to Practice for Arboriculture", Figure2.RightToPractice.arboriculture, "#E377C2"),  # pink
            ("Right to Practice for Urban Forestry", Figure2.RightToPractice.urban_forestry, "#8C8C8C"),  # gray
        ],
    ),
]

# Pre-calc map extent size to compute sensible offsets for leader lines
bounds = provinces.total_bounds  # (xmin, ymin, xmax, ymax)
xspan = bounds[2] - bounds[0]
yspan = bounds[3] - bounds[1]
# offsets as fractions of the map span
xoff_fraction = 0.06
yoff_fraction = 0.03

for ax, (title, groups) in zip(axes, panel_specs):
    # Plot base: all province boundaries
    provinces.boundary.plot(ax=ax, color='black', linewidth=0.25)

    # Plot each subgroup with its own color
    legend_patches = []
    for label, acronyms, color in groups:
        mask = provinces['ACRONYM'].isin(acronyms)
        if mask.any():
            provinces[mask].plot(ax=ax, color=color, edgecolor='black')
            legend_patches.append(Patch(facecolor=color, edgecolor='black', label=label))

    # Labels: annotate each selected province with either centered text or offset with leader for Atlantic provinces
    # We'll label all provinces that appear in any group on this panel.
    panel_acronyms = set().union(*[set(acrs) for _, acrs, _ in groups])
    selected = provinces[provinces['ACRONYM'].isin(panel_acronyms)]

    for _, row in selected.iterrows():
        acr = row['ACRONYM']
        centroid = row.geometry.centroid
        cx, cy = centroid.x, centroid.y

        # If Atlantic province -> offset text to the right (or slightly above) with a connecting line
        if acr in atlantic:
            # compute an offset that scales to map extent
            x_off = xspan * xoff_fraction
            y_off = yspan * yoff_fraction

            # Choose a slight vertical shift depending on province so labels don't overlap each other
            # (quick heuristic)
            if acr == 'NL':
                text_xy = (cx + x_off, cy + y_off * 1.0)
            elif acr == 'PE':
                text_xy = (cx + x_off, cy + y_off * 1.5)
            elif acr == 'NS':
                text_xy = (cx + x_off, cy - y_off * 0.5)
            else:  # NB
                text_xy = (cx + x_off, cy - y_off * 1.0)

            ax.annotate(
                acr,
                xy=(cx, cy),
                xytext=text_xy,
                fontsize=10,
                fontweight='bold',
                ha='left',
                va='center',
                arrowprops=dict(arrowstyle='-', linewidth=0.8, color='black', shrinkA=0, shrinkB=0),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)
            )
        else:
            # default: place label at centroid
            ax.text(cx, cy, acr, fontsize=10, ha='center', va='center', fontweight='bold')

    # Title & styling
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_axis_off()

    # Add legend for this panel (outside lower-left of the panel)
    if legend_patches:
        ax.legend(handles=legend_patches, loc='lower left', frameon=True, fontsize=9)

# layout adjustments
plt.tight_layout()
plt.subplots_adjust(top=0.88)  # make room for suptitle
plt.show()
