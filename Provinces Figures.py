import matplotlib.pyplot as plt
import geopandas as gpd

# Load shapefile
provinces = gpd.read_file('Shapefile/Simplified provinces - 1 km.gpkg')

# Province acronyms mapping
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

# --- Filter for BC, ON, QC ---
target_acronyms = ['BC', 'ON', 'QC']

# Map province names to acronyms
provinces['ACRONYM'] = provinces['PRNAME'].map(province_accronyms)

# Filter only the three provinces
selected = provinces[provinces['ACRONYM'].isin(target_acronyms)]

# --- Plot ---
fig, ax = plt.subplots(figsize=(8, 6))
provinces.boundary.plot(ax=ax, color='black', linewidth=0.25)  # outline all provinces
selected.plot(ax=ax, color='cornflowerblue')

# Annotate labels
for _, row in selected.iterrows():
    centroid = row.geometry.centroid
    ax.text(centroid.x, centroid.y, row['ACRONYM'], fontsize=12, ha='center', fontweight='bold')

# Style adjustments
ax.set_title('Selected Canadian Provinces: BC, ON, and QC', fontsize=14, fontweight='bold')
ax.set_axis_off()

plt.tight_layout()
plt.show()
