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
def plot_1x2_panels(
        panel_definitions,
        gdf=provinces,
        figsize=(14, 6),
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
        nrows=1,
        ncols=2,
):
    if len(panel_definitions) != nrows * ncols:
        raise ValueError(f"panel_definitions must have {nrows * ncols} items for a {nrows}x{ncols} grid.")

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

    # create 1x2 axes
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
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
            # Skip subtitle entries
            if settings.get('is_subtitle', False):
                continue
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

        # Add legend for this panel
        if legend_items:
            panel_legend_handles = []
            subtitle_indices = []
            seen_labels = set()  # Track unique labels

            for idx, (label, settings) in enumerate(legend_items.items()):
                clean_label = label.strip()  # Remove trailing/leading spaces

                # Check if this is a subtitle
                if settings.get('is_subtitle', False):
                    # Add extra spacing before "Some Activities"
                    if clean_label == "Some Activities":
                        # Add invisible spacer
                        panel_legend_handles.append(Patch(
                            facecolor='none',
                            edgecolor='none',
                            label=' '
                        ))

                    # Add subtitle as text-only entry
                    panel_legend_handles.append(Patch(
                        facecolor='none',
                        edgecolor='none',
                        label=clean_label
                    ))
                    subtitle_indices.append(len(panel_legend_handles) - 1)
                else:
                    # Regular legend entry with color - only add if not seen before
                    if clean_label not in seen_labels:
                        seen_labels.add(clean_label)
                        panel_legend_handles.append(Patch(
                            facecolor=settings['color'],
                            edgecolor='black',
                            linestyle=settings.get('linestyle', 'solid'),
                            label=clean_label
                        ))

            # Set different bbox_to_anchor based on panel
            if panel_idx == 0:
                bbox_anchor = (1.05, .80)  # Lower for panel 0
            else:
                bbox_anchor = (1.05, .85)  # Higher for panel 1

            legend = ax.legend(handles=panel_legend_handles,
                               loc='upper right',
                               bbox_to_anchor=bbox_anchor,
                               frameon=False,
                               fontsize=13,
                               ncol=1)

            # Make subtitle entries bold
            for i in subtitle_indices:
                legend.get_texts()[i].set_weight('bold')

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
# Define panels - ONLY 2 PANELS FOR 1x2 GRID
# -------------------------
panel_definitions = [
    ("Right to Title", ['BC', 'AB', 'SK', 'ON', 'QC', 'NL', 'NS', 'NB']),
    ("Right to Practice", ['BC', 'ON', 'QC', 'NS', 'NB', 'MB', 'SK']),
]

# Define colors per panel with subtitles for panel 1
panel_legend_items = {
    0: {
        'Registered Professional Forester': {
            "color": "#006400",
            "acronyms": ['BC', 'ON', 'QC', 'AB', 'SK'],
            "text_color": "white"
        },
        'Registered Professional Forester ': {
            "color": "#006400",
            "acronyms": ['NL', 'NS', 'NB'],
            "text_color": "black"
        },
        'Arborist': {
            "color": "#8FBC8F",
            "acronyms": ['AB', 'SK'],
            "text_color": "black"
        }
    },
    1: {
        "All Activities": {
            "is_subtitle": True,
            "color": "none",
            "acronyms": []
        },
        "Urban forestry": {
            "color": "#006400",
            "acronyms": ['BC', 'QC'],
            "text_color": "white"
        },
        "Some Activities": {
            "is_subtitle": True,
            "color": "none",
            "acronyms": []
        },
        "Urban forestry ": {
            "color": "#8FBC8F",
            "acronyms": ['ON'],
            "text_color": "black"
        },
        "Arboriculture": {
            "color": "#ADD8E6",
            "acronyms": ['MB', 'SK'],
            "text_color": "black"
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
        'line_start': (8245714.44, 2492888.93)
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
fig, axes = plot_1x2_panels(
    panel_definitions=panel_definitions,
    gdf=provinces,
    figsize=(14, 6),
    pad=0.045,
    north_extra=0.09,
    atlantic_manual_offsets=None,
    per_province=per_province_example,
    panel_legend_items=panel_legend_items,
    title_y=.92,
    save_path='Figures/Figure 3 - Rights to Title and Practice.pdf',
    nrows=1,
    ncols=2
)