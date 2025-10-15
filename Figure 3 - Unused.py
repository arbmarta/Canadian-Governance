import warnings
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.patches import Patch
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import os

# --- Load provinces (adjust path as needed) ---
provinces = gpd.read_file('Shapefile/Simplified provinces - 10 km.gpkg')

# --- Acronyms mapping (same as before) ---
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


def plot_map_with_icons_below_labels(
    fire_icon_path="Figures/fire.png",
    warn_icon_path="Figures/warning.png",
    target_acronyms=None,
    gdf=provinces,
    figsize=(10, 10),
    pad=0.04,
    north_extra=0.08,
    atlantic_offset_x_frac=0.06,
    atlantic_offset_y_frac=0.03,
    atlantic_manual_offsets=None,
    legend_items=None,
    legend_loc='upper right',
    fire_size_pct=8.0,
    warn_size_pct=8.0,
    per_province=None,
    icon_nudge_x_frac=0.0,
    icon_vertical_gap_frac=0.02,
    icon_zoom_mode='pct',  # currently only 'pct' supported (zoom = pct/100)
    save_path=None,
    verbose=True
):
    """
    Robust single-panel map that plots province acronyms and places icon images below the label.
    - Fixes handling when per_province[acr]['xy'] is None.
    - per_province entry example:
        per_province = {
            'BC': {'xy': (x,y), 'fontsize': 13, 'bbox': True, 'label_offset': (dx,dy)},
            'NL': {'xy': None, 'fontsize': 10, 'bbox': False}
        }
      If 'xy' is None or missing, the function falls back to default centroid/atlantic placement.
    - fire_size_pct, warn_size_pct : percent used as OffsetImage zoom = pct/100.
    """

    # ---- validate icon files ----
    if not os.path.isfile(fire_icon_path):
        raise FileNotFoundError(f"Fire icon not found: {fire_icon_path}")
    if not os.path.isfile(warn_icon_path):
        raise FileNotFoundError(f"Warning icon not found: {warn_icon_path}")

    fire_img = mpimg.imread(fire_icon_path)
    warn_img = mpimg.imread(warn_icon_path)

    # ---- selection for bbox/plotting ----
    if target_acronyms is None:
        selected = gdf[gdf['ACRONYM'].notna()].copy()
    else:
        selected = gdf[gdf['ACRONYM'].isin(target_acronyms)].copy()

    if selected.empty:
        raise ValueError("No provinces found for the provided acronyms / mapping.")

    # ---- bbox + padding + north_extra ----
    xmin, ymin, xmax, ymax = selected.total_bounds
    xpad = (xmax - xmin) * pad
    ypad = (ymax - ymin) * pad
    xmin_p, xmax_p = xmin - xpad, xmax + xpad
    ymin_p = ymin - ypad
    ymax_p = ymax + ypad + (ymax - ymin) * north_extra

    # ---- default colour groups ----
    grey_acrs = {'AB', 'SK', 'NL', 'NB', 'NS'}
    dark_green_acrs = {'BC', 'QC'}
    light_green_acrs = {'ON'}
    other_color = "white"

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

    # ---- override colors with legend_items if provided (and build legend handles) ----
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

    # ---- prepare per_province defaults and atlantic offsets ----
    if per_province is None:
        per_province = {}
    if atlantic_manual_offsets is None:
        atlantic_manual_offsets = {}

    # ---- spans for offsets and icon spacing ----
    bounds = gdf.total_bounds
    xspan = bounds[2] - bounds[0] if (bounds[2] - bounds[0]) != 0 else 1.0
    yspan = bounds[3] - bounds[1] if (bounds[3] - bounds[1]) != 0 else 1.0
    x_off = xspan * atlantic_offset_x_frac
    y_off = yspan * atlantic_offset_y_frac
    icon_vertical_gap = yspan * icon_vertical_gap_frac

    # ---- icon target sets ----
    fire_acrs = {'BC', 'AB', 'SK', 'MB'}
    warn_acrs = {'BC', 'ON'}

    # ---- compute zoom factors ----
    if icon_zoom_mode != 'pct':
        raise ValueError("Only icon_zoom_mode='pct' is supported currently.")
    fire_zoom = max(0.0, float(fire_size_pct)) / 100.0
    warn_zoom = max(0.0, float(warn_size_pct)) / 100.0

    # ---- helper to add icons ----
    def add_icon(ax, img_arr, xy, zoom=0.05, zorder=12):
        im = OffsetImage(img_arr, zoom=zoom)
        ab = AnnotationBbox(im, xy, frameon=False, pad=0.0, box_alignment=(0.5, 0.5), zorder=zorder)
        ax.add_artist(ab)

    # ---- helper to validate xy tuples ----
    def validate_xy(xy):
        if xy is None:
            return False
        try:
            if hasattr(xy, '__iter__') and len(xy) == 2:
                # ensure numeric
                x0, y0 = xy
                float(x0); float(y0)
                return True
            return False
        except Exception:
            return False

    # ---- base map plotting ----
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    gdf.boundary.plot(ax=ax, color='black', linewidth=0.25, zorder=1)
    gdf_plot = gdf.copy()
    gdf_plot['fill_color'] = gdf_plot['ACRONYM'].map(acr_to_color).fillna(other_color)
    gdf_plot.plot(ax=ax, color=gdf_plot['fill_color'], edgecolor='black', linewidth=0.35, zorder=2)

    atlantic_set = {'NL', 'PE', 'NS', 'NB'}

    # ---- iterate and place labels/icons ----
    for _, row in gdf[gdf['ACRONYM'].notna()].iterrows():
        acr = row['ACRONYM']

        # Determine label position:
        label_xy_valid = False
        if acr in per_province and 'xy' in per_province:
            if validate_xy(per_province[acr]['xy']):
                label_x, label_y = per_province[acr]['xy']
                label_xy_valid = True
            else:
                if verbose:
                    warnings.warn(f"per_province['{acr}']['xy'] is missing or invalid (value={per_province[acr].get('xy')}). Falling back to default placement.")
                # fall through to other placement options

        if not label_xy_valid:
            if acr in atlantic_manual_offsets and validate_xy(atlantic_manual_offsets[acr]):
                label_x, label_y = atlantic_manual_offsets[acr]
            elif acr in atlantic_set:
                centroid = row.geometry.centroid
                cx, cy = centroid.x, centroid.y
                if acr == 'NL':
                    label_x, label_y = cx + x_off, cy + y_off * 1.0
                elif acr == 'PE':
                    label_x, label_y = cx + x_off, cy + y_off * 1.5
                elif acr == 'NS':
                    label_x, label_y = cx + x_off, cy - y_off * 0.5
                else:  # NB
                    label_x, label_y = cx + x_off, cy - y_off * 1.0
            else:
                centroid = row.geometry.centroid
                label_x, label_y = centroid.x, centroid.y

        # apply label_offset if present and valid
        if acr in per_province and 'label_offset' in per_province[acr]:
            off = per_province[acr]['label_offset']
            if validate_xy(off):
                dx, dy = off
                label_x += dx
                label_y += dy
            else:
                if verbose:
                    warnings.warn(f"per_province['{acr}']['label_offset'] is invalid (value={off}). Ignoring this offset.")

        # fontsize and bbox flag
        fontsize = per_province.get(acr, {}).get('fontsize', 11)
        bbox_flag = per_province.get(acr, {}).get('bbox', True)

        # draw label
        if bbox_flag:
            bbox_kwargs = dict(boxstyle="round,pad=0.12", fc="#F5F5F5", ec='none', alpha=0.95)
            ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5, bbox=bbox_kwargs)
        else:
            ax.text(label_x, label_y, acr, fontsize=fontsize, ha='center', va='center', fontweight='bold', zorder=5)

        # compute icon stacking coordinates below label
        icon_x = label_x + (xspan * icon_nudge_x_frac)
        y_fire = label_y - icon_vertical_gap
        y_warn_below_fire = y_fire - icon_vertical_gap

        has_fire = (acr in fire_acrs)
        has_warn = (acr in warn_acrs)

        if has_fire:
            add_icon(ax, fire_img, (icon_x, y_fire), zoom=fire_zoom, zorder=11)
            if has_warn:
                add_icon(ax, warn_img, (icon_x, y_warn_below_fire), zoom=warn_zoom, zorder=12)
        else:
            if has_warn:
                add_icon(ax, warn_img, (icon_x, y_fire), zoom=warn_zoom, zorder=12)

    # ---- legend ----
    if legend_handles:
        ax.legend(handles=legend_handles, loc=legend_loc, frameon=True, fontsize=9)

    # final extent/styling
    ax.set_xlim(xmin_p, xmax_p)
    ax.set_ylim(ymin_p, ymax_p)
    ax.set_axis_off()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()
    return fig, ax


# -----------------------
# Example usage (safe):
# -----------------------
per_province_example = {
    # If you want to override XY, supply a valid tuple (x,y) in your map CRS.
    # If you don't want to override, either omit 'xy' or set it to None (the function will fallback).
    'BC': {'xy': None, 'fontsize': 13, 'bbox': True},
    'NL': {'xy': None, 'fontsize': 10, 'bbox': True},
    # 'ON': {'xy': (-79.5, 45.5), 'fontsize': 11, 'bbox': False}  # if you want manual coords
}

legend_items_example = {
    "No Right to Title or Right to Practice for urban forestry activities": ("white", ['MB', 'PEI', 'YT', 'NT', 'NU']),
    "Right to Title but no Right to Practice for urban forestry activities": ("#808080", ['AB','SK','NL','NB','NS']),
    "Right to Title and Right to Practice for all urban forestry activities": ("#006400", ['BC','QC']),
    "Right to Title and Right to Practice for some urban forestry activities": ("#8FBC8F", ['ON']),
}

fig, ax = plot_map_with_icons_below_labels(
    fire_icon_path="Figures/fire.png",
    warn_icon_path="Figures/warning.png",
    target_acronyms=None,
    pad=0.05,
    north_extra=0.09,
    atlantic_manual_offsets=None,
    legend_items=legend_items_example,
    legend_loc='upper right',
    fire_size_pct=4.0,   # 8% of native image size (tweak until it looks right)
    warn_size_pct=4.0,
    per_province=per_province_example,
    icon_nudge_x_frac=0.0,
    icon_vertical_gap_frac=0.02,
    figsize=(10,10),
    save_path=None,
    verbose=True
)
