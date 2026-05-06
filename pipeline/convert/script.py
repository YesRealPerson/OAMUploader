"""
Convert GeoTIFF to Cloud-Optimized GeoTIFF (COG)
 - From shared directory, read GeoTIFF, convert to COG, store, delete unconverted
"""
import sys
import traceback
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

def convert_to_cog(src_path, dst_path, profile_name: str = "deflate"):
    output_profile = cog_profiles.get(profile_name)
    output_profile.update({"compress": profile_name, "level": 1, "bigtiff": "YES"})
    
    config = dict(
        GDAL_NUM_THREADS=2, 
        GDAL_TIFF_INTERNAL_MASK=False, # CHANGED: Disabling this reduces IO pressure
        GDAL_TIFF_OVR_BLOCKSIZE=512,
        GDAL_CACHEMAX=1024, # Increased slightly to buffer more data
        GDAL_REPORTS_PROGRESS="ON",
        CPL_DEBUG="ON",
        # Force GDAL to be more patient with the file system
        GDAL_FILENAME_IS_UTF8="YES",
        TIFF_USE_OVR= "TRUE"
    )
    
    cog_translate(
        src_path, 
        dst_path, 
        output_profile, 
        config=config, 
        in_memory=False, 
        quiet=False, 
        allow_intermediate_compression=True 
    )
# C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\tester1.tif
# C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\tester1_convert.tif
if __name__ == "__main__":
    try:
        convert_to_cog(sys.argv[1], sys.argv[2])
    except Exception as e:
        traceback.print_exc()
        print(e)
        sys.exit(1)
