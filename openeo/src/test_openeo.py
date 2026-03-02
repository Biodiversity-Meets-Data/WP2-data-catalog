import openeo
import pystac
from datetime import datetime
import rasterio
import rasterio.warp
from rasterio.plot import show

# url to the tiff file
tiff_url = "https://files.isric.org/soilgrids/latest/data_aggregated/5000m/bdod/bdod_0-5cm_mean_5000.tif"

# datetime of the tiff file
# In case your data spans multiple days, you can use the datetime of the first day of the data
# When specifying a temporal range in load_stac later on, the stac item will be filteren only on this datetime
dt = datetime.fromisoformat("1905-04-01")

# desired output path for the stac item
output_path = "bdod-stac-item.json"

with rasterio.open(tiff_url) as src:
    proj_bounds = list(src.bounds)
    left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    item = pystac.Item(
        id="bdod-stac-item",
        geometry={
            "type": "Polygon",
            "coordinates": [[
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top],
                [left, bottom]
            ]]
        },
        bbox=[left, bottom, right, top],
        datetime= dt,
        properties={ # These properties are optional, but can speed up the loading of the data.
            "proj:epsg": src.crs.to_epsg(),
            "proj:shape": src.shape, # Caveat: this is [height, width] and not [width, height] if you want to set them yourself
            "proj:bbox": proj_bounds,
        },
        stac_extensions=[
            "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        ],
        assets={
            "ndvi": pystac.Asset(
                href=tiff_url,
                title="Normalized Difference Vegetation Index",
                extra_fields={
                    "eo:bands": [ # REQUIRED: define the bands in the eo extension for openEO to be able to load it
                        {
                            "name": "NDVI-band",
                        }
                    ],
                }
            )
        }
    )
    item.validate()
    item.save_object(dest_href=output_path, include_self_link=False)