import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd

# -------------------------
# Load data & mapping
# -------------------------
gpkg_path = 'Shapefile/Simplified provinces - 10 km.gpkg'
provinces = gpd.read_file(gpkg_path)

province_acronyms = {
    'Newfoundland and Labrador / Terre-Neuve-et-Labrador': 'NL',
    'Prince Edward Island / Île-du-Prince-Édouard': 'PEI',
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
provinces['ACRONYM'] = provinces['PRNAME'].map(province_acronyms)


# -------------------------
# Main plotting function
# -------------------------
def plot_2x2_panels(
        panel_definitions,
        gdf=provinces,
        figsize=(14, 12),
        pad=0.04,
        north_extra=0.09,
        atlantic_offset_x_frac=0.06,
        atlantic_offset_y_frac=0.03,
        atlantic_manual_offsets=None,
        per_province=None,
        panel_legend_items=None,
        title_y=0.98,
        legend_bbox=(0.75, 0.96),
        label_bbox=False,
        save_path=None,
):
    if len(panel_definitions) != 4:
        raise ValueError("panel_definitions must be a list/tuple of 4 items (2x2 grid).")

    per_province = per_province or {}
    atlantic_manual_offsets = atlantic_manual_offsets or {}
    panel_legend_items = panel_legend_items or {}

    def validate_xy(xy):
        if xy is None:
            return False
        try:
            if hasattr(xy, '__iter__') and len(xy) == 2:
                float(xy[0]);
                float(xy[1])
                return True
        except Exception:
            return False
        return False

    # Compute GLOBAL bounds ONCE for all panels (no zoom)
    overall_bounds = gdf.total_bounds
    xmin, ymin, xmax, ymax = overall_bounds
    overall_xspan = xmax - xmin if (xmax - xmin) != 0 else 1.0
    overall_yspan = ymax - ymin if (ymax - ymin) != 0 else 1.0

    # Apply padding to global extent
    xpad = overall_xspan * pad
    ypad = overall_yspan * pad
    xmin_p = xmin - xpad
    xmax_p = xmax + xpad
    ymin_p = ymin - ypad
    ymax_p = ymax + ypad + overall_yspan * north_extra

    x_off_global = overall_xspan * atlantic_offset_x_frac
    y_off_global = overall_yspan * atlantic_offset_y_frac

    # create 2x2 axes
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    # iterate panels
    for panel_idx, (ax, (title, panel_acronyms)) in enumerate(zip(axes, panel_definitions)):
        # Get panel-specific legend items if provided
        legend_items = panel_legend_items.get(panel_idx, {})

        # Build color map for this panel
        acr_to_color = {}
        acr_to_linestyle = {}
        for acr in gdf['ACRONYM'].dropna().unique():
            acr_to_color[acr] = 'white'
            acr_to_linestyle[acr] = 'solid'

        # Apply legend colors to this panel
        for label, settings in legend_items.items():
            color = settings['color']
            acrs = settings['acronyms']
            linestyle = settings.get('linestyle', 'solid')
            for a in acrs:
                acr_to_color[a] = color
                acr_to_linestyle[a] = linestyle

        # base map boundaries (context)
        gdf.boundary.plot(ax=ax, color='black', linewidth=0.25, zorder=1)

        # prepare plot coloring: fill only panel-selected provinces
        gdf_plot = gdf.copy()
        gdf_plot['fill_color'] = 'white'
        gdf_plot['edge_style'] = 'solid'

        for _, row in gdf_plot.iterrows():
            acr = row['ACRONYM']
            if acr in panel_acronyms:
                gdf_plot.loc[gdf_plot['ACRONYM'] == acr, 'fill_color'] = acr_to_color.get(acr, 'white')
                gdf_plot.loc[gdf_plot['ACRONYM'] == acr, 'edge_style'] = acr_to_linestyle.get(acr, 'solid')

        # Plot provinces with appropriate styling
        for _, row in gdf_plot.iterrows():
            linestyle = row['edge_style']
            color = row['fill_color']
            gdf_plot[gdf_plot.index == row.name].plot(
                ax=ax,
                color=color,
                edgecolor='black',
                linewidth=0.35,
                linestyle=linestyle,
                zorder=2
            )

        # labels for all provinces
        atlantic_set = {'NL', 'PE', 'NS', 'NB'}
        for _, row in gdf[gdf['ACRONYM'].notna()].iterrows():
            acr = row['ACRONYM']

            # compute label position
            if acr in per_province and 'xy' in per_province and validate_xy(per_province[acr]['xy']):
                label_x, label_y = per_province[acr]['xy']
            elif acr in atlantic_manual_offsets and validate_xy(atlantic_manual_offsets[acr]):
                label_x, label_y = atlantic_manual_offsets[acr]
            elif acr in atlantic_set:
                centroid = row.geometry.centroid
                cx, cy = centroid.x, centroid.y
                if acr == 'NL':
                    label_x, label_y = cx + x_off_global, cy + y_off_global * 1.0
                elif acr == 'PE':
                    label_x, label_y = cx + x_off_global, cy + y_off_global * 1.5
                elif acr == 'NS':
                    label_x, label_y = cx + x_off_global, cy - y_off_global * 0.5
                else:  # NB
                    label_x, label_y = cx + x_off_global, cy - y_off_global * 1.0
            else:
                centroid = row.geometry.centroid
                label_x, label_y = centroid.x, centroid.y

            # apply label_offset if provided
            if acr in per_province and 'label_offset' in per_province and validate_xy(
                    per_province[acr]['label_offset']):
                dx, dy = per_province[acr]['label_offset']
                label_x += dx
                label_y += dy

            # fontsize and bbox
            fontsize = per_province.get(acr, {}).get('fontsize', 10)
            bbox_flag = per_province.get(acr, {}).get('bbox', label_bbox)
            if bbox_flag:
                bbox_kwargs = dict(boxstyle="round,pad=0.12", fc="#F5F5F5", ec='none', alpha=0.95)
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5,
                        bbox=bbox_kwargs)
            else:
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5)

        # title for the panel
        ax.set_title(title, fontsize=11, fontweight='bold', y=title_y)

        # Add legend for this panel (skip panel 3)
        if legend_items and panel_idx != 3:
            panel_legend_handles = []
            for label, settings in legend_items.items():
                panel_legend_handles.append(Patch(
                    facecolor=settings['color'],
                    edgecolor='black',
                    linestyle=settings.get('linestyle', 'solid'),
                    label=label
                ))
            ax.legend(handles=panel_legend_handles,
                      loc='upper right',
                      bbox_to_anchor=(0.98, 0.85),
                      frameon=False,
                      fontsize=10)

        # ALL PANELS USE THE SAME EXTENT (no zoom)
        ax.set_xlim(xmin_p, xmax_p)
        ax.set_ylim(ymin_p, ymax_p)
        ax.set_axis_off()

    plt.tight_layout(rect=[0, 0, 1, 1])
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    return fig, axes


# -------------------------
# Define panels with custom coloring per panel
# -------------------------
panel_definitions = [
    ("Forestry Professional\nRegulatory Organizations", ['BC', 'AB', 'SK', 'ON', 'QC', 'NL', 'NS', 'NB']),
    ("Apprenticeship and\nSkilled Trades Agencies", ['BC', 'ON', 'QC', 'NS', 'NB']),
    ("International Society\nof Arboriculture Chapters", ['BC', 'AB', 'SK', 'MB', 'ON', 'QC', 'NL', 'PEI', 'NS', 'NB']),
    ("Other Arboricultural\nProfessional Associations", ['BC', 'ON', 'MB']),
]

# Define colors per panel
panel_legend_items = {
    0: {
        "PRO engaged in urban forestry": {
            "color": "#006400",
            "acronyms": ['BC', 'ON', 'QC']
        },
        "PRO not engaged in urban forestry": {
            "color": "#8FBC8F",
            "acronyms": ['AB', 'SK', 'NL', 'NS', 'NB']
        }
    },
    1: {
        "In effect": {
            "color": "#006400",
            "acronyms": ['BC', 'ON', 'NS', 'NB']
        },
        "Coming into effect": {
            "color": "#8FBC8F",
            "acronyms": ['QC']
        },
    },
    2: {
        "Pacific Northwest Chapter": {
            "color": "#009DAE",
            "acronyms": ['BC']
        },
        "Prairie Chapter": {
            "color": "#DFAF2C",
            "acronyms": ['AB', 'SK', 'MB'],
        },
        "Ontario Chapter": {
            "color": "#D02E2E",
            "acronyms": ['ON']
        },
        "Quebec Chapter": {
            "color": "#003DA5",
            "acronyms": ['QC']
        },
        "Atlantic Chapter": {
            "color": "#0F52BA",
            "acronyms": ['NL', 'PEI', 'NS', 'NB']
        }
    },
    3: {
        "Dark green (BC)": {
            "color": "#006400",
            "acronyms": ['BC', 'MB', 'ON']
        }
    }
}

per_province_example = {
    'BC': {'fontsize': 12},
    'NL': {'fontsize': 9}
}

# -------------------------
# Run plotting
# -------------------------
fig, axes = plot_2x2_panels(
    panel_definitions=panel_definitions,
    gdf=provinces,
    figsize=(14, 12),
    pad=0.045,
    north_extra=0.09,
    atlantic_manual_offsets=None,
    per_province=per_province_example,
    panel_legend_items=panel_legend_items,
    title_y=.95,
    legend_bbox=(0.75, 0.85),
    label_bbox=False,
    save_path=None
)