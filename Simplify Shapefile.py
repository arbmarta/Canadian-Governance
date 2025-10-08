import geopandas as gpd
import matplotlib.pyplot as plt

# Original shapefile
gdf = gpd.read_file("Shapefile/Provinces.gpkg")

# Standardize province codes
mapping = {"N.L.": "NL", "P.E.I.": "PE", "N.S.": "NS", "N.B.": "NB",
           "Que.": "QC", "Ont.": "ON", "Man.": "MB", "Sask.": "SK",
           "Alta.": "AB", "B.C.": "BC", "Y.T.": "YT", "N.W.T.": "NT", "Nvt.": "NU"}
gdf["PREABBR"] = gdf["PREABBR"].replace(mapping)

# Simplify geometry
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.5, preserve_topology=True)

# Save simplified version
gdf.to_file("Shapefile/Provinces_simplified.gpkg", driver="GPKG")

# Print summary
print(f"Original vertices: {gdf.geometry.apply(lambda x: len(x.exterior.coords) if hasattr(x, 'exterior') else 0).sum()}")
print(f"Simplified saved to: Shapefile/Provinces_simplified.gpkg")

# Show simplified map
gdf.plot(edgecolor="black", color="#d0e3f0")
plt.title("Simplified Provinces (Tolerance = 0.5)")
plt.axis("off")
plt.show()