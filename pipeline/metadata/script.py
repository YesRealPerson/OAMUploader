"""
Extract metadata
 - GeoTIFF metadata via GDAL
 - Generate thumbnail
 - Store in appropriate shared folder
"""
import os
from rio_cogeo import cog_info
import rasterio
import sys
from rasterio.enums import Resampling

def extract_metadata(path, out_dir):
    # Generate thumbnail
    with rasterio.open(path) as src:
        thumbnail_path = os.path.join(out_dir, "thumbnail.png")
        scale = max(src.width, src.height) / 1000
        data = src.read(out_shape=(src.count, int(src.height/scale), int(src.width/scale)), resampling=Resampling.bilinear)
        # may have four bands
        count = 3
        if data.shape[0] > 3:
            data = data[:3]
        # may have less than 3 bands
        if data.shape[0] < 3:
            count = 1
            data = data[:1]
        
        with rasterio.open(thumbnail_path, 'w', driver="PNG", height=int(src.height/scale), width=int(src.width/scale), count=count, dtype="uint8") as dst: # validation ensures dtype
            dst.write(data)
    
    metadata_path = os.path.join(out_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        md = cog_info(path).model_dump_json(exclude_none=True, by_alias=True)
        f.write(md)

# C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1\\tester1.tif
# C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1
extract_metadata(sys.argv[1], sys.argv[2])