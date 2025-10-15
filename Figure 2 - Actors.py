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
        icon_vertical_gap_frac=0.02,
        legend_items=None,
        legend_loc='upper right',
        save_path=None,
        verbose=True
):

    if len(panel_definitions) != 4:
        raise ValueError("panel_definitions must be a list/tuple of 4 items (2x2 grid).")

    per_province = per_province or {}
    atlantic_manual_offsets = atlantic_manual_offsets or {}

    # color assignment defaults
    grey_acrs = {'AB', 'SK', 'NL', 'NB', 'NS'}
    dark_green_acrs = {'BC', 'QC'}
    light_green_acrs = {'ON'}
    other_color = "#D3D3D3"

    acr_to_color = {}
    for acr in gdf['ACRONYM'].dropna().unique():
        if acr in grey_acrs:
            acr_to_color[acr] = "#808080"
        elif acr in dark_green_acrs:
            acr_to_color[acr] = "#006400"
        elif acr in light_green_acrs:
            acr_to_color[acr] = "#8FBC8F"
        else:
            acr_to_color[acr] = other_color

    # override with legend_items if provided
    legend_handles = []
    if legend_items:
        for label, (color, acrs) in legend_items.items():
            for a in acrs:
                acr_to_color[a] = color
            legend_handles.append(Patch(facecolor=color, edgecolor='black', label=label))
    else:
        legend_handles.append(Patch(facecolor="#808080", edgecolor='black', label="AB / SK / NL / NB / NS"))
        legend_handles.append(Patch(facecolor="#006400", edgecolor='black', label="BC / QC"))
        legend_handles.append(Patch(facecolor="#8FBC8F", edgecolor='black', label="ON"))
        legend_handles.append(Patch(facecolor=other_color, edgecolor='black', label="Other"))

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
    icon_vertical_gap = overall_yspan * icon_vertical_gap_frac

    # create 2x2 axes
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    # iterate panels
    for ax, (title, panel_acronyms) in zip(axes, panel_definitions):
        # base map boundaries (context)
        gdf.boundary.plot(ax=ax, color='black', linewidth=0.25, zorder=1)

        # prepare plot coloring: fill only panel-selected provinces
        gdf_plot = gdf.copy()
        gdf_plot['fill_color'] = other_color
        for acr in gdf_plot['ACRONYM'].dropna().unique():
            if acr in panel_acronyms:
                gdf_plot.loc[gdf_plot['ACRONYM'] == acr, 'fill_color'] = acr_to_color.get(acr, other_color)
        gdf_plot.plot(ax=ax, color=gdf_plot['fill_color'], edgecolor='black', linewidth=0.35, zorder=2)

        # labels for all provinces
        atlantic_set = {'NL', 'PE', 'NS', 'NB'}
        for _, row in gdf[gdf['ACRONYM'].notna()].iterrows():
            acr = row['ACRONYM']

            # compute label position
            label_xy_valid = False
            if acr in per_province and 'xy' in per_province and validate_xy(per_province[acr]['xy']):
                label_x, label_y = per_province[acr]['xy']
                label_xy_valid = True
            elif acr in atlantic_manual_offsets and validate_xy(atlantic_manual_offsets[acr]):
                label_x, label_y = atlantic_manual_offsets[acr]
                label_xy_valid = True
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
                label_xy_valid = True
            else:
                centroid = row.geometry.centroid
                label_x, label_y = centroid.x, centroid.y
                label_xy_valid = True

            # apply label_offset if provided
            if acr in per_province and 'label_offset' in per_province and validate_xy(
                    per_province[acr]['label_offset']):
                dx, dy = per_province[acr]['label_offset']
                label_x += dx
                label_y += dy

            # fontsize and bbox
            fontsize = per_province.get(acr, {}).get('fontsize', 10)
            bbox_flag = per_province.get(acr, {}).get('bbox', True)
            if bbox_flag:
                bbox_kwargs = dict(boxstyle="round,pad=0.12", fc="#F5F5F5", ec='none', alpha=0.95)
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5,
                        bbox=bbox_kwargs)
            else:
                ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5)

        # title for the panel
        ax.set_title(title, fontsize=11, fontweight='bold')

        # ALL PANELS USE THE SAME EXTENT (no zoom)
        ax.set_xlim(xmin_p, xmax_p)
        ax.set_ylim(ymin_p, ymax_p)
        ax.set_axis_off()

    # overall legend
    if legend_handles:
        fig.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(0.98, 0.96), frameon=True, fontsize=9)

    plt.tight_layout(rect=[0, 0, 0.98, 0.98])
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    return fig, axes


# -------------------------
# Define panels
# -------------------------
panel_definitions = [
    ("Professional Regulatory Organizations", ['BC', 'SK']),
    ("Skilled Trade Agencies", ['BC', 'ON', 'QC', 'NS', 'NB']),
    ("ISA Chapter", ['BC', 'AB', 'SK', 'MB', 'ON']),
    ("Other Arboricultural Professional Associations", ['BC', 'ON', 'MB']),
]

per_province_example = {
    'BC': {'xy': None, 'fontsize': 12, 'bbox': True},
    'NL': {'xy': None, 'fontsize': 9, 'bbox': True}
}

legend_items_example = {
    "Grey (AB/SK/NL/NB/NS)": ("#808080", ['AB', 'SK', 'NL', 'NB', 'NS']),
    "Dark green (BC/QC)": ("#006400", ['BC', 'QC']),
    "Light green (ON)": ("#8FBC8F", ['ON']),
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
    icon_vertical_gap_frac=0.02,
    legend_items=legend_items_example,
    legend_loc='upper right',
    save_path=None,
    verbose=True
)