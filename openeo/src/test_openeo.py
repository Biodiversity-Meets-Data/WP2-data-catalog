from urllib import parse
import pystac
from datetime import datetime
import rasterio
import rasterio.warp
from shapely.geometry import Polygon, mapping


def convert_item(url, name):
    print(f"converting {url}")

    dt = datetime.fromisoformat("1905-04-01")
    start_datetime = dt
    end_datetime = datetime.fromisoformat("2016-07-05")
    output_path = f"../data/{name}.json"

    with rasterio.open(url) as src:
        proj_bounds = list(src.bounds)
    left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    polygon = mapping(Polygon([
        [left, bottom],
        [right, bottom],
        [right, top],
        [left, top],
        [left, bottom]
    ]))

    item = pystac.Item(
        id="bdod-stac-item",
        geometry=polygon,
        bbox=[left, bottom, right, top],
        datetime=dt,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
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
            "bdod": pystac.Asset(
                href=url,
                title="SoilGrids250m 2.0 - Bulk density aggregated 5000m",
                extra_fields={
                    "eo:bands": [ # REQUIRED: define the bands in the eo extension for openEO to be able to load it
                        {
                            "name": "bdod-band",
                        }
                    ],
                }
            )
        }
    )
    item.validate()
    item.save_object(dest_href=output_path, include_self_link=False)


# base url
bdod_url = "https://files.isric.org/soilgrids/latest/data_aggregated/5000m/bdod/"
# url to the tiff files
bdod_tiffs = ["bdod_0-5cm_mean_5000.tif",
              "bdod_5-15cm_mean_5000.tif",
              "bdod_15-30cm_mean_5000.tif",
              "bdod_30-60cm_mean_5000.tif",
              "bdod_60-100cm_mean_5000.tif",
              "bdod_100-200cm_mean_5000.tif"]
bdod_urls = list()

for bdod_tiff in bdod_tiffs:
    url = parse.urljoin(bdod_url, bdod_tiff)
    bdod_urls.append(url)
    convert_item(url, bdod_tiff)
