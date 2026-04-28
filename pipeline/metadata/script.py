"""
Extract metadata
 - GeoTIFF metadata via GDAL
 - Generate thumbnail
 - Store in appropriate shared folder
"""
import os
import sys
import json
from datetime import datetime, timezone
import rasterio
from rasterio.enums import Resampling
from pystac import Item, Asset, MediaType
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.file import FileExtension
from rasterio.warp import transform_bounds

def extract_metadata(tiff_path, meta_path, out_dir, item_id, s3_path, baseurl, userid):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(meta_path, 'r') as f:
        user_md = json.load(f)

    with rasterio.open(tiff_path) as src:
        # 1. Handle Thumbnail Generation
        thumbnail_path = os.path.join(out_dir, "thumbnail.png")
        scale = max(src.width, src.height) / 1000
        out_shape = (src.count, int(src.height / scale), int(src.width / scale))
        
        data = src.read(out_shape=out_shape, resampling=Resampling.bilinear)
        # Ensure 1 or 3 bands for PNG
        count = 3 if data.shape[0] >= 3 else 1
        data = data[:count]

        with rasterio.open(
            thumbnail_path, 'w', driver="PNG", 
            height=out_shape[1], width=out_shape[2], 
            count=count, dtype=src.profile['dtype']
        ) as dst:
            dst.write(data)

        # 2. Extract Spatial/Temporal Info
        bbox_wgs84 = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
        # Simplified geometry polygon
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [bbox_wgs84[0], bbox_wgs84[1]],
                [bbox_wgs84[2], bbox_wgs84[1]],
                [bbox_wgs84[2], bbox_wgs84[3]],
                [bbox_wgs84[0], bbox_wgs84[3]],
                [bbox_wgs84[0], bbox_wgs84[1]]
            ]]
        }

        # 3. Initialize STAC Item
        item = Item(
            id=item_id,
            geometry=geometry,
            bbox=list(bbox_wgs84),
            datetime=datetime.now(timezone.utc) , # Or extract from TIFF tags
            properties={
                "title": user_md.get('title'),
                "description": user_md.get('tags'),
                "gsd": src.res[0], 
                "oam:platform_type": user_md.get('platform'),
                "oam:producer_name": user_md.get('provider'),
                "oam:uploaderid": userid,
                "license": user_md.get('license'),
                "instruments": [user_md.get('sensor')],
                # TODO: When we get user auth we can add more provider metadata
                "contact": user_md.get('contact'),
            },
            collection="openaerialmap"
        )

        # 4. Add Extensions
        item.stac_extensions.append("https://hotosm.github.io/stactools-hotosm/oam/v0.1.0/schema.json")
        
        # Add Projection Extension info
        proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.epsg = src.crs.to_epsg()
        proj_ext.shape = [src.height, src.width]
        proj_ext.transform = list(src.transform)[:6]

        # 5. Add Assets
        filename = s3_path.split("/")[-1]
        baseurl = baseurl +"/"+ "/".join(s3_path.split("/")[:-1])
        file_stats = os.stat(tiff_path)
        tiff_asset = Asset(
            href=baseurl+"/cog-"+filename,
            media_type=MediaType.COG,
            roles=["data"],
            title=user_md.get('title')
        )
        thumbnail_asset = Asset(
            href=baseurl+"/thumbnail.png",
            media_type=MediaType.PNG,
            roles=["thumbnail"],
            title="thumbnail"
        )
        meta_asset = Asset(
            href=baseurl+"/metadata.json",
            media_type=MediaType.JSON,
            roles=["metadata"],
            title="metadata"
        )
        item.add_asset("visual", tiff_asset)
        item.add_asset("metadata", meta_asset)
        item.add_asset("thumbnail", thumbnail_asset)
        FileExtension.ext(tiff_asset, add_if_missing=True).size = file_stats.st_size

        # 6. Save Item
        item_path = os.path.join(out_dir, "metadata.json")
        item.save_object(dest_href=item_path)
        print(f"STAC Item saved to {item_path}")

if __name__ == "__main__":
    # Usage: python script.py <path_to_tiff> <output_dir> <item_id>
    extract_metadata(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
    # py .\script.py C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1\\tester1.tif C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1\\meta.json C:\\Users\\Stephen\\Desktop\\OAMUploader\\Repo\\temporary\\tester1 iojsdajsd testbucket/23871929/asdasdasdad/tester1.tif http://localhost:4566