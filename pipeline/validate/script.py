"""
Validate GeoTIFF
"""
import sys
import rasterio
def validate_geotiff(path):
    with rasterio.open(path) as src:
        # The dataset’s coordinate reference system
        # If does not exist, not georeferenced
        if src.crs is None:
            sys.exit(5)
        # Number of bands
        if src.count > 4:
            sys.exit(6)
        # Bit depth should match uint8 like the example file
        for type in src.dtypes:
            if type != 'uint8':
                sys.exit(7)
    return True

# C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\tester1.tif
print(validate_geotiff(sys.argv[1]))