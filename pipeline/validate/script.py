"""
Validate GeoTIFF
"""
import sys
import rasterio
import traceback
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
if __name__ == "__main__":
    try:
        print(validate_geotiff(sys.argv[1]))
    except Exception as e:
        traceback.print_exc()
        print(e)
        sys.exit(1)