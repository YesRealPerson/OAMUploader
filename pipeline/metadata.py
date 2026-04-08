"""
Extract metadata
 - GeoTIFF metadata via GDAL
 - Generate thumbnail
 - Store in appropriate shared folder
"""
def extract_metadata(path, out_dir):
    if not os.path.exists(path):
        return None
    try:
        src = rasterio.open(path)
    except:
        return None
    
    metadata = {}
    metadata["width"] = src.width
    metadata["height"] = src.height
    metadata["count"] = src.count
    metadata["crs"] = str(src.crs)
    metadata["bounds"] = list(src.bounds) 

    thumbnail_path = os.path.join(out_dir, "thumbnail.tif")
    try:
        data = src.read(out_shape=(src.count, 256, 256))
        profile = src.profile
        profile.update({"height": 256, "width": 256})
        dest = rasterio.open(thumbnail_path, "w", driver="GTiff", height=256, width=256, count=src.count, dtype=src.dtypes[0])
        dest.write(data)
        dest.close()
        metadata["thumbnail"] = thumbnail_path
    except:
        metadata["thumbnail"] = None

    metadata_path = os.path.join(out_dir, "metadata.json")
    try:
        file = open(metadata_path, "w")
        json.dump(metadata, file)
        file.close()
    except:
        pass
    src.close()
    return metadata
