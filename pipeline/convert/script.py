"""
Convert GeoTIFF to Cloud-Optimized GeoTIFF (COG)
 - From shared directory, read GeoTIFF, convert to COG, store, delete unconverted
"""
import sys
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

def convert_to_cog(src_path, dst_path, profile: str = "deflate"):
    try:
        output_profile = cog_profiles.get(profile)
        config = dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_INTERNAL_MASK=True, GDAL_TIFF_OVR_BLOCKSIZE="128")
        cog_translate(src_path, dst_path, output_profile, config=config, in_memory=False, quiet=True)
        return True;
    except:
        return False;

# C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\tester1.tif
# C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\tester1_convert.tif
print(convert_to_cog(sys.argv[1], sys.argv[2]))