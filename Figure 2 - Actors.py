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
                float(xy[0])
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

    # Print CRS and label coordinates for ALL provinces
    print(f"GeoDataFrame CRS: {gdf.crs}")
    print("\n" + "=" * 70)
    print("PROVINCE LABEL COORDINATES")
    print("=" * 70)

    atlantic_set = {'NL', 'PEI', 'NS', 'NB'}

    for _, row in gdf[gdf['ACRONYM'].notna()].iterrows():
        acr = row['ACRONYM']

        # Compute label position (same logic as in plotting)
        if acr in per_province and 'xy' in per_province[acr] and validate_xy(per_province[acr]['xy']):
            label_x, label_y = per_province[acr]['xy']
            source = "per_province override"
        elif acr in atlantic_manual_offsets and validate_xy(atlantic_manual_offsets.get(acr)):
            label_x, label_y = atlantic_manual_offsets[acr]
            source = "atlantic_manual_offsets"
        elif acr in atlantic_set:
            centroid = row.geometry.centroid
            cx, cy = centroid.x, centroid.y
            if acr == 'NL':
                label_x, label_y = cx + x_off_global, cy + y_off_global * 1.0
            elif acr == 'PEI':
                label_x, label_y = cx + x_off_global, cy + y_off_global * 1.5
            elif acr == 'NS':
                label_x, label_y = cx + x_off_global, cy - y_off_global * 0.5
            else:  # NB
                label_x, label_y = cx + x_off_global, cy - y_off_global * 1.0
            source = "Atlantic offset calculation"
        else:
            centroid = row.geometry.centroid
            label_x, label_y = centroid.x, centroid.y
            source = "Centroid"

        # Apply label_offset if provided
        if acr in per_province and 'label_offset' in per_province[acr] and validate_xy(
                per_province[acr]['label_offset']):
            dx, dy = per_province[acr]['label_offset']
            label_x += dx
            label_y += dy
            source += " + label_offset"

        print(f"{acr:4s}: ({label_x:12.2f}, {label_y:12.2f})  [{source}]")

    print("=" * 70 + "\n")

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
        acr_to_text_color = {}
        for acr in gdf['ACRONYM'].dropna().unique():
            acr_to_color[acr] = 'white'
            acr_to_linestyle[acr] = 'solid'
            acr_to_text_color[acr] = 'black'

        # Apply legend colors to this panel
        for label, settings in legend_items.items():
            color = settings['color']
            acrs = settings['acronyms']
            linestyle = settings.get('linestyle', 'solid')
            text_color = settings.get('text_color', 'black')
            for a in acrs:
                acr_to_color[a] = color
                acr_to_linestyle[a] = linestyle
                acr_to_text_color[a] = text_color

        # base map boundaries (context) - plot once
        gdf.boundary.plot(ax=ax, color='black', linewidth=0.25, zorder=1)

        # prepare plot coloring: fill only panel-selected provinces
        gdf_plot = gdf.copy()
        gdf_plot['fill_color'] = 'white'
        gdf_plot['edge_style'] = 'solid'

        # Vectorized assignment instead of iterrows
        for acr in panel_acronyms:
            mask = gdf_plot['ACRONYM'] == acr
            gdf_plot.loc[mask, 'fill_color'] = acr_to_color.get(acr, 'white')
            gdf_plot.loc[mask, 'edge_style'] = acr_to_linestyle.get(acr, 'solid')

        # Group by style to minimize plot calls
        for (color, linestyle), group in gdf_plot.groupby(['fill_color', 'edge_style']):
            group.plot(
                ax=ax,
                color=color,
                edgecolor='black',
                linewidth=0.35,
                linestyle=linestyle,
                zorder=2
            )

        # labels for all provinces
        for _, row in gdf[gdf['ACRONYM'].notna()].iterrows():
            acr = row['ACRONYM']

            # Get the actual centroid
            centroid = row.geometry.centroid
            cx, cy = centroid.x, centroid.y

            # compute label position
            if acr in per_province and 'xy' in per_province[acr] and validate_xy(per_province[acr]['xy']):
                label_x, label_y = per_province[acr]['xy']
            elif acr in atlantic_manual_offsets and validate_xy(atlantic_manual_offsets.get(acr)):
                label_x, label_y = atlantic_manual_offsets[acr]
            elif acr in atlantic_set:
                if acr == 'NL':
                    label_x, label_y = cx + x_off_global, cy + y_off_global * 1.0
                elif acr == 'PEI':
                    label_x, label_y = cx + x_off_global, cy + y_off_global * 1.5
                elif acr == 'NS':
                    label_x, label_y = cx + x_off_global, cy - y_off_global * 0.5
                else:  # NB
                    label_x, label_y = cx + x_off_global, cy - y_off_global * 1.0
            else:
                label_x, label_y = cx, cy

            # apply label_offset if provided
            if acr in per_province and 'label_offset' in per_province[acr] and validate_xy(
                    per_province[acr]['label_offset']):
                dx, dy = per_province[acr]['label_offset']
                label_x += dx
                label_y += dy

            # Draw leader line if enabled
            draw_leader = per_province.get(acr, {}).get('leader_line', False)
            if draw_leader:
                # Get line start point (can be offset from centroid)
                line_start = per_province.get(acr, {}).get('line_start', None)
                if line_start and validate_xy(line_start):
                    line_x, line_y = line_start
                else:
                    line_x, line_y = cx, cy

                # Only draw if label is significantly offset
                if abs(label_x - line_x) > 1000 or abs(label_y - line_y) > 1000:
                    ax.plot([line_x, label_x], [line_y, label_y],
                            color='black', linewidth=0.5, linestyle='-',
                            alpha=0.6, zorder=4)

            # fontsize and bbox
            fontsize = per_province.get(acr, {}).get('fontsize', 10)
            bbox_flag = per_province.get(acr, {}).get('bbox', label_bbox)
            text_color = acr_to_text_color.get(acr, 'black')

            if bbox_flag:
                bbox_kwargs = dict(boxstyle="round,pad=0.12", fc="#F5F5F5", ec='none', alpha=0.95)
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center',
                        fontweight='bold', zorder=5, color=text_color, bbox=bbox_kwargs)
            else:
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center',
                        fontweight='bold', zorder=5, color=text_color)

        # title for the panel
        ax.set_title(title, fontsize=16, fontweight='bold', y=title_y)

        # Add legend for this panel (skip panel 3)
        if legend_items and panel_idx != 3:
            panel_legend_handles = []
            seen_labels = set()  # Track unique labels
            for label, settings in legend_items.items():
                clean_label = label.strip()  # Remove trailing/leading spaces
                if clean_label not in seen_labels:
                    seen_labels.add(clean_label)
                    panel_legend_handles.append(Patch(
                        facecolor=settings['color'],
                        edgecolor='black',
                        linestyle=settings.get('linestyle', 'solid'),
                        label=clean_label  # Use cleaned label
                    ))
            ax.legend(handles=panel_legend_handles,
                      loc='upper right',
                      bbox_to_anchor=(1.05, 0.90),
                      frameon=False,
                      fontsize=14)

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
        "Engaged in\nurban forestry": {
            "color": "#006400",
            "acronyms": ['BC', 'ON', 'QC'],
            "text_color": "white"  # White text on dark green
        },
        "Not engaged in\nurban forestry": {
            "color": "#8FBC8F",
            "acronyms": ['AB', 'SK', 'NL', 'NS', 'NB'],
            "text_color": "black"  # Black text on light green
        }
    },
    1: {
        "In force": {
            "color": "#006400",
            "acronyms": ['NS', 'NB'],
            "text_color": "black"
        },
        "In force ": {
            "color": "#006400",
            "acronyms": ['BC', 'ON'],
            "text_color": "white"
        },
        "Coming into force": {
            "color": "#8FBC8F",
            "acronyms": ['QC'],
            "text_color": "black"
        },
    },
    2: {
        "Pacific Northwest": {
            "color": "#009DAE",
            "acronyms": ['BC'],
            "text_color": "white"
        },
        "Prairie": {
            "color": "#DFAF2C",
            "acronyms": ['AB', 'SK', 'MB'],
            "text_color": "black"
        },
        "Ontario": {
            "color": "#D02E2E",
            "acronyms": ['ON'],
            "text_color": "white"
        },
        "Quebec": {
            "color": "#001A4D",
            "acronyms": ['QC'],
            "text_color": "white"
        },
        "Atlantic": {
            "color": "#4A90E2",
            "acronyms": ['NL', 'PEI', 'NS', 'NB'],
            "text_color": "black"  # Black text for Atlantic provinces
        }
    },
    3: {
        "Dark green (BC)": {
            "color": "#006400",
            "acronyms": ['BC', 'MB', 'ON'],
            "text_color": "white"
        }
    }
}

per_province_example = {
    'BC': {'fontsize': 12},
    'QC': {'fontsize': 12},
    'AB': {'fontsize': 12},
    'SK': {'fontsize': 12},
    'MB': {'fontsize': 12},

    'YT': {'xy': (4233952.37, 3695000.25), 'fontsize': 12},
    'NT': {'xy': (4927480.76, 3328827.18), 'fontsize': 12},
    'NU': {'xy': (5983431.05, 3209827.33), 'fontsize': 12},
    'ON': {'xy': (6645027.05, 1642475.10), 'fontsize': 12},

    # Atlantic provinces with leader lines
    'NL': {
        'xy': (8545714.44, 2732888.93),
        'fontsize': 12,
        'leader_line': False,
        'line_start': (8245714.44, 2492888.93)  # Offset from centroid
    },
    'PEI': {
        'xy': (8876373.85, 1734420.28),
        'fontsize': 12,
        'leader_line': False,
        'line_start': (8576373.85, 1784420.28)
    },
    'NS': {
        'xy': (8627052.60, 1373934.28),
        'fontsize': 12,
        'leader_line': False,
        'line_start': (8419100.60, 1425934.28)
    },
    'NB': {
        'xy': (7997731.26, 1194444.35),
        'fontsize': 12,
        'leader_line': False,
        'line_start': (8337731.26, 1414444.35)
    },
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
    title_y=.92,
    save_path='Figures/Figure 2 - Actors.pdf'
)