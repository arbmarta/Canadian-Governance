import matplotlib.pyplot as plt
import geopandas as gpd

# Load shapefile
provinces = gpd.read_file('Shapefile/Provinces.shp')
print(provinces.crs)

# Simplify geometries
# tolerance controls how much simplification is applied (higher = simpler, faster)
# try values like 0.01, 0.05, or 0.1 for degrees; or project first if needed
provinces['geometry'] = provinces['geometry'].simplify(tolerance=10000, preserve_topology=True)

# Save simplified version to GeoPackage
provinces.to_file('Shapefile/Simplified provinces - 10 km.gpkg', driver='GPKG')

# Plot simplified shapes
fig, ax = plt.subplots(figsize=(10, 8))
provinces.plot(ax=ax, color='lightblue', edgecolor='black')
ax.set_title('Simplified Provinces')
ax.set_axis_off()
plt.tight_layout()
plt.show()