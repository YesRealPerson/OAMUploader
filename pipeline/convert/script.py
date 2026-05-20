"""
Convert GeoTIFF to Cloud-Optimized GeoTIFF (COG)
 - From shared directory, read GeoTIFF, convert to COG, store, delete unconverted
"""
import os
import sys
import traceback
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

def convert_to_cog(src_path, dst_path, profile_name: str = "deflate"):
    os.makedirs("/data/tmp", exist_ok=True)
    output_profile = cog_profiles.get(profile_name).copy()
    output_profile.update({
        "compress": "deflate",
        "level": 1,
        "bigtiff": "YES",
        "blocksize": 512,
        "predictor": 2,
        "sparse_ok": True,
    })

    config = {
        "GDAL_NUM_THREADS": "2",
        "GDAL_CACHEMAX": 512,
        "CPL_TMPDIR": "/data/tmp",
        "TMPDIR": "/data/tmp",
        "BIGTIFF_OVERVIEW": "YES",
        "GDAL_TIFF_OVR_BLOCKSIZE": "512",
        "GDAL_TIFF_INTERNAL_MASK": "NO",
        "CHECK_DISK_FREE_SPACE": "FALSE",
    }

    cog_translate(
        src_path,
        dst_path,
        output_profile,
        config=config,
        in_memory=False,
        quiet=False,
        allow_intermediate_compression=True,
        overview_resampling="nearest",
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
