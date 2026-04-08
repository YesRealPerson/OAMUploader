"""
(2)
Validate GeoTIFF
 - From shared directory, read GeoTIFF and validate, if invalid delete
"""
import os
import rasterio
def validate_geotiff(path):
    if not os.path.exists(path):
        return False
    try:
        src = rasterio.open(path)
    except:
        try:
            os.remove(path)
        except:
            pass
        return False
    def delete(path):
        src.close()
        os.remove(path)
        return False
    if src.driver != "GTiff":
        return delete(path)
    if src.crs is None:
        return delete(path)
    if src.count == 0:
        return delete(path)
    src.close()
    return True

print(validate_geotiff("C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1\\tester1.tif"))